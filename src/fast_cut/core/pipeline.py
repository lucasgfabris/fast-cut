"""Orquestrador do pipeline de processamento."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Tuple

from .config import Config
from .file_manager import FileManager
from .protocols import Analyzer, Cutter, Downloader
from .types import ProcessingStats

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Orquestra o fluxo: download -> análise -> corte -> limpeza."""

    def __init__(
        self,
        config: Config,
        downloader: Downloader,
        analyzer: Analyzer,
        cutter: Cutter,
        file_manager: FileManager,
    ) -> None:
        self._config = config
        self._downloader = downloader
        self._analyzer = analyzer
        self._cutter = cutter
        self._file_manager = file_manager

    def run(
        self,
        max_videos_per_channel: int = 5,
        skip_download: bool = False,
    ) -> ProcessingStats:
        """Executa o pipeline completo."""
        stats = ProcessingStats()
        stats.clips_by_platform = {
            platform: 0 for platform in self._config.platform_specs
        }

        # Etapa 1: Download
        videos = self._download_phase(max_videos_per_channel, skip_download)
        stats.downloaded_videos = len(videos)

        if not videos:
            logger.error("Nenhum vídeo disponível para processamento")
            return stats

        # Etapa 2: Análise e Corte
        self._processing_phase(videos, stats)

        # Etapa 3: Limpeza
        self._cleanup_phase()

        return stats

    def process_single_video(self, video_path: Path) -> ProcessingStats:
        """Processa um único vídeo já disponível localmente."""
        stats = ProcessingStats()
        stats.clips_by_platform = {
            platform: 0 for platform in self._config.platform_specs
        }

        logger.info("Processando: %s", video_path.name)

        clips = self._analyzer.find_best_clips(video_path)

        if not clips:
            logger.warning("Nenhum clipe interessante encontrado")
            return stats

        stats.analyzed_videos = 1
        logger.info("%d clipes encontrados", len(clips))

        results = self._cutter.process_clips(clips, video_path, 1, 1)

        video_clips_count = 0
        for platform, platform_clips in results.items():
            count = len(platform_clips)
            stats.clips_by_platform[platform] += count
            video_clips_count += count

        stats.generated_clips += video_clips_count
        return stats

    # -- Fases internas -------------------------------------------------------

    def _download_phase(
        self, max_videos_per_channel: int, skip_download: bool
    ) -> List[Path]:
        """Fase de download de vídeos."""
        logger.info("ETAPA 1: DOWNLOAD DE VÍDEOS")

        if skip_download:
            videos = self._file_manager.get_existing_videos()
            logger.info("Usando %d vídeos existentes", len(videos))
        else:
            videos = self._downloader.download_from_channels(max_videos_per_channel)
            logger.info("%d vídeos baixados", len(videos))

        return videos

    def _process_single_video_task(
        self, video_path: Path, index: int, total: int
    ) -> Tuple[int, int, dict[str, int], List[str]]:
        """Processa um vídeo individual (executado em thread).

        Returns:
            Tuple de (analyzed_count, clips_count, clips_by_platform, errors)
        """
        analyzed = 0
        clips_count = 0
        errors: List[str] = []
        clips_by_platform: dict[str, int] = {}

        progress = (index / total) * 100
        logger.info(
            "Processando %d/%d (%.1f%%): %s",
            index,
            total,
            progress,
            video_path.name,
        )

        try:
            clips = self._analyzer.find_best_clips(video_path)

            if not clips:
                logger.warning(
                    "Nenhum clipe interessante encontrado em %s",
                    video_path.name,
                )
                errors.append(f"Sem clipes em {video_path.name}")
                return analyzed, clips_count, clips_by_platform, errors

            analyzed = 1

            results = self._cutter.process_clips(clips, video_path, index, total)

            for platform, platform_clips in results.items():
                count = len(platform_clips)
                clips_by_platform[platform] = count
                clips_count += count

            logger.info(
                "%d clipes gerados para %s",
                clips_count,
                video_path.name,
            )

        except Exception as e:
            error_msg = f"Erro em {video_path.name}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

        return analyzed, clips_count, clips_by_platform, errors

    def _processing_phase(self, videos: List[Path], stats: ProcessingStats) -> None:
        """Fase de processamento dos vídeos (paralelo via threads)."""
        logger.info("ETAPA 2: ANÁLISE E GERAÇÃO DE CORTES")

        total_videos = len(videos)

        # Processamento paralelo - FFmpeg roda em subprocessos, então threads
        # funcionam bem aqui (não há GIL blocking para subprocess)
        max_workers = min(2, total_videos)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    self._process_single_video_task,
                    video_path,
                    i,
                    total_videos,
                ): video_path
                for i, video_path in enumerate(videos, 1)
            }

            for future in as_completed(futures):
                video_path = futures[future]
                try:
                    (
                        analyzed,
                        clips_count,
                        clips_by_platform,
                        errors,
                    ) = future.result()

                    stats.analyzed_videos += analyzed
                    stats.generated_clips += clips_count
                    stats.errors.extend(errors)

                    for platform, count in clips_by_platform.items():
                        stats.clips_by_platform[platform] = (
                            stats.clips_by_platform.get(platform, 0) + count
                        )

                except Exception as e:
                    error_msg = f"Erro inesperado em {video_path.name}: {e}"
                    logger.error(error_msg)
                    stats.errors.append(error_msg)

    def _cleanup_phase(self) -> None:
        """Fase de limpeza."""
        logger.info("ETAPA 3: LIMPEZA")

        self._downloader.cleanup()
        self._cutter.cleanup()
        self._file_manager.cleanup_temp_videos()
