"""Sistema principal do Fast Cut (facade)."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import Config
from .file_manager import FileManager
from .pipeline import PipelineOrchestrator
from .protocols import Analyzer, Cutter, Downloader
from .reporter import Reporter
from .types import ProcessingStats, VideoMetadata

logger = logging.getLogger(__name__)


class FastCutSystem:
    """Facade do sistema - ponto de entrada para todas as operações."""

    def __init__(
        self,
        config: Config,
        downloader: Downloader,
        analyzer: Analyzer,
        cutter: Cutter,
        show_header: bool = True,
    ) -> None:
        self._config = config
        self._config.create_directories()

        self._file_manager = FileManager(config)
        self._reporter = Reporter(config)
        self._pipeline = PipelineOrchestrator(
            config=config,
            downloader=downloader,
            analyzer=analyzer,
            cutter=cutter,
            file_manager=self._file_manager,
        )
        self._downloader = downloader

        if show_header:
            self._reporter.print_header()

    def run_full_pipeline(
        self,
        max_videos_per_channel: int = 5,
        skip_download: bool = False,
    ) -> ProcessingStats:
        """Executa o pipeline completo."""
        try:
            start_time = datetime.now()

            stats = self._pipeline.run(
                max_videos_per_channel=max_videos_per_channel,
                skip_download=skip_download,
            )

            duration = datetime.now() - start_time
            self._reporter.print_final_report(stats, duration)

            return stats

        except Exception as e:
            error_msg = f"Erro crítico no pipeline: {e}"
            logger.error(error_msg)
            stats = ProcessingStats()
            stats.errors.append(error_msg)
            return stats

    def process_specific_video(self, video_path_str: str) -> ProcessingStats:
        """Processa um vídeo específico (arquivo local ou URL do YouTube)."""
        logger.info("PROCESSAMENTO DE VÍDEO ESPECÍFICO")

        # Resolve o vídeo (URL ou caminho local)
        video_path = self._resolve_video(video_path_str)
        if video_path is None:
            return ProcessingStats()

        try:
            start_time = datetime.now()

            stats = self._pipeline.process_single_video(video_path)

            duration = datetime.now() - start_time
            self._reporter.print_video_report(stats, duration)

            return stats

        except Exception as e:
            error_msg = f"Erro ao processar vídeo: {e}"
            logger.error(error_msg)
            stats = ProcessingStats()
            stats.errors.append(error_msg)
            return stats

    def clear_all_outputs(self) -> None:
        """Limpa todas as pastas de saída e temporários."""
        self._file_manager.clear_all_outputs()

    def list_channels(self) -> None:
        """Lista canais autorizados."""
        logger.info("CANAIS AUTORIZADOS:")

        if not self._config.authorized_channels:
            logger.error("Nenhum canal configurado")
            logger.info("Configure AUTHORIZED_CHANNELS no arquivo .env")
            return

        for i, channel_id in enumerate(self._config.authorized_channels, 1):
            logger.info("%d. %s", i, channel_id)

            try:
                videos = self._downloader.get_channel_videos(channel_id, 1)
                if videos:
                    logger.info("   Ativo - último: %s...", videos[0].title[:50])
                else:
                    logger.warning("   Sem vídeos recentes")
            except Exception:
                logger.error("   Erro de acesso")

        logger.info("Total: %d canais", len(self._config.authorized_channels))

    def test_system(self) -> None:
        """Testa o sistema com vídeo existente."""
        logger.info("TESTE DO SISTEMA")

        videos = self._file_manager.get_existing_videos()

        if not videos:
            logger.error("Nenhum vídeo para teste")
            logger.info("Coloque um vídeo em: %s", self._config.temp_dir)
            return

        test_video = videos[0]
        logger.info("Testando com: %s", test_video.name)

        try:
            stats = self._pipeline.process_single_video(test_video)
            logger.info("%d clipes de teste gerados", stats.generated_clips)
        except Exception as e:
            logger.error("Erro no teste: %s", e)

    # -- Helpers internos -----------------------------------------------------

    def _resolve_video(self, video_path_str: str) -> Optional[Path]:
        """Resolve uma string para um Path de vídeo (URL ou local)."""
        if video_path_str.startswith(("http://", "https://", "www.")):
            logger.info("Link detectado: %s", video_path_str)
            logger.info("Baixando vídeo...")

            try:
                video_metadata = VideoMetadata(
                    id="",
                    title="Video específico",
                    url=video_path_str,
                    duration=None,
                    upload_date=None,
                    view_count=None,
                    channel_id="",
                )

                video_path = self._downloader.download_video(video_metadata)

                if not video_path:
                    logger.error("Falha ao baixar o vídeo")
                    return None

                logger.info("Vídeo baixado: %s", video_path.name)
                return video_path

            except Exception as e:
                logger.error("Erro ao baixar vídeo: %s", e)
                return None
        else:
            video_path = Path(video_path_str)

            if not video_path.exists():
                logger.error("Vídeo não encontrado: %s", video_path)
                return None

            if not video_path.is_file():
                logger.error("Caminho não é um arquivo: %s", video_path)
                return None

            return video_path


def create_system(
    config: Optional[Config] = None, show_header: bool = True
) -> FastCutSystem:
    """Factory que monta o sistema com implementações padrão."""
    from ..services.analyzer import VideoAnalyzer
    from ..services.cutter import VideoCutter
    from ..services.downloader import VideoDownloader

    cfg = config or Config.from_env()
    cfg.create_directories()

    return FastCutSystem(
        config=cfg,
        downloader=VideoDownloader(cfg),
        analyzer=VideoAnalyzer(cfg),
        cutter=VideoCutter(cfg),
        show_header=show_header,
    )
