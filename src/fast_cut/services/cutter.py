"""Serviço de corte de vídeos."""

import logging
from pathlib import Path
from typing import List, Optional

from ..core.config import Config
from ..core.protocols import Transcriber
from ..core.types import Clip, ProcessingResults
from ..utils.ffmpeg import FFmpegError, FFmpegUtils

logger = logging.getLogger(__name__)


class CuttingError(Exception):
    """Erro específico de corte."""

    pass


class VideoCutter:
    """Serviço responsável pelo corte e otimização de vídeos."""

    def __init__(
        self,
        config: Config,
        transcriber: Optional[Transcriber] = None,
    ) -> None:
        self._config = config
        self._ffmpeg = FFmpegUtils()
        self._transcriber = transcriber
        self._config.create_directories()

    def process_clips(
        self,
        clips: List[Clip],
        source_video: Path,
        video_num: int = 1,
        total_videos: int = 1,
    ) -> ProcessingResults:
        """Processa uma lista de clipes para todas as plataformas."""
        if not self._ffmpeg.is_available:
            raise CuttingError("FFmpeg não está disponível")

        results: ProcessingResults = {
            platform: [] for platform in self._config.platform_specs
        }

        # Extrai o video_id do nome do arquivo
        video_name = source_video.stem
        if video_name.startswith("fastcut_original_"):
            video_id = video_name.replace("fastcut_original_", "")
        else:
            video_id = video_name

        total_clips = len(clips)

        for i, clip in enumerate(clips, 1):
            clip_progress = (i / total_clips) * 100
            logger.info(
                "Processando clipe %d/%d (%.1f%%)",
                i,
                total_clips,
                clip_progress,
            )

            try:
                for platform in self._config.platform_specs:
                    platform_dir = self._config.output_dir / platform
                    output_path = (
                        platform_dir / f"fastcut_cut_{video_id}_{i}_{platform}.mp4"
                    )

                    if self._cut_and_optimize(
                        source_video, clip, platform, output_path
                    ):
                        # Queima legendas se habilitado
                        if self._should_add_subtitles():
                            self._burn_subtitles(output_path, platform)

                        results[platform].append(str(output_path))

            except Exception as e:
                logger.error("Erro no clipe %d: %s", i, e)

        return results

    def _should_add_subtitles(self) -> bool:
        """Verifica se deve adicionar legendas."""
        return self._config.subtitles_enabled and self._transcriber is not None

    def _burn_subtitles(self, video_path: Path, platform: str) -> None:
        """Transcreve e queima legendas no vídeo."""
        if self._transcriber is None:
            return

        spec = self._config.platform_specs[platform]
        ass_path = video_path.with_suffix(".ass")

        try:
            # 1. Transcreve o clip
            words = self._transcriber.transcribe(video_path)

            if not words:
                logger.warning("Nenhuma fala detectada em %s", video_path.name)
                return

            # 2. Gera o arquivo .ass
            self._transcriber.generate_ass(words, ass_path, spec.resolution)

            # 3. Re-encoda com legenda queimada
            temp_output = video_path.with_name(f"_sub_{video_path.name}")

            # Escapa backslashes e dois-pontos no path do ASS
            # para o filtro do FFmpeg no Windows
            ass_str = str(ass_path).replace("\\", "/")
            ass_str = ass_str.replace(":", "\\:")

            args = [
                "-i",
                str(video_path),
                "-vf",
                f"ass={ass_str}",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "18",
                "-c:a",
                "copy",
                "-movflags",
                "+faststart",
                "-y",
                str(temp_output),
            ]

            self._ffmpeg.run_command(args)

            # 4. Substitui o original pelo legendado
            if temp_output.exists():
                video_path.unlink()
                temp_output.rename(video_path)
                logger.info("Legenda aplicada: %s", video_path.name)

        except FFmpegError as e:
            logger.error(
                "Erro ao queimar legenda em %s: %s",
                video_path.name,
                e,
            )
        finally:
            # Limpa arquivos temporários de legenda
            ass_path.unlink(missing_ok=True)
            temp = video_path.with_name(f"_sub_{video_path.name}")
            temp.unlink(missing_ok=True)

    def _cut_and_optimize(
        self,
        source_video: Path,
        clip: Clip,
        platform: str,
        output_path: Path,
    ) -> bool:
        """Corta e otimiza um clipe em um único passo de encoding.

        Combina seek, scale/crop e encode em um único comando FFmpeg,
        evitando a perda de qualidade de uma dupla codificação.
        """
        try:
            spec = self._config.platform_specs[platform]
            w, h = spec.resolution

            # Scale para cobrir a resolução alvo, depois crop centralizado
            vf = (
                f"scale={w}:{h}"
                f":force_original_aspect_ratio=increase,"
                f"crop={w}:{h}:(iw-{w})/2:(ih-{h})/2"
            )

            args = [
                "-ss",
                str(clip.start_time),
                "-i",
                str(source_video),
                "-t",
                str(clip.duration),
                "-vf",
                vf,
                "-r",
                str(spec.fps),
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "18",
                "-c:a",
                "aac",
                "-b:a",
                self._config.audio_bitrate,
                "-movflags",
                "+faststart",
                "-y",
                str(output_path),
            ]

            self._ffmpeg.run_command(args)

            if output_path.exists():
                logger.info(
                    "Otimizado para %s: %s",
                    platform,
                    output_path.name,
                )
                return True

            return False

        except FFmpegError as e:
            logger.error("Erro na otimização para %s: %s", platform, e)
            return False

    def cleanup(self) -> None:
        """Remove arquivos temporários de corte."""
        try:
            for pattern in [
                "fastcut_temp_*.mp4",
                "temp-audio*",
                "*.ass",
                "_sub_*.mp4",
            ]:
                for file in self._config.temp_dir.glob(pattern):
                    file.unlink()
            logger.info("Arquivos temporários de corte removidos")
        except Exception as e:
            logger.warning("Erro na limpeza: %s", e)
