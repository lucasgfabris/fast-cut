"""Serviço de corte de vídeos."""

import logging
from pathlib import Path
from typing import List

from ..core.config import Config
from ..core.types import Clip, ProcessingResults
from ..utils.ffmpeg import FFmpegError, FFmpegUtils

logger = logging.getLogger(__name__)


class CuttingError(Exception):
    """Erro específico de corte."""

    pass


class VideoCutter:
    """Serviço responsável pelo corte e otimização de vídeos."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._ffmpeg = FFmpegUtils()
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

            temp_clip = self._config.temp_dir / f"fastcut_temp_{video_id}_{i}.mp4"

            try:
                self._cut_clip(source_video, clip, temp_clip)

                for platform in self._config.platform_specs:
                    platform_dir = self._config.output_dir / platform
                    output_path = (
                        platform_dir / f"fastcut_cut_{video_id}_{i}_{platform}.mp4"
                    )

                    if self._optimize_for_platform(temp_clip, platform, output_path):
                        results[platform].append(str(output_path))

            except Exception as e:
                logger.error("Erro no clipe %d: %s", i, e)
            finally:
                temp_clip.unlink(missing_ok=True)

        return results

    def _cut_clip(self, video_path: Path, clip: Clip, output_path: Path) -> None:
        """Corta um clipe do vídeo."""
        args = [
            "-i",
            str(video_path),
            "-ss",
            str(clip.start_time),
            "-t",
            str(clip.duration),
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-preset",
            "fast",
            "-crf",
            "23",
            "-y",
            str(output_path),
        ]

        try:
            self._ffmpeg.run_command(args)

            if not output_path.exists():
                raise CuttingError("Arquivo de saída não foi criado")

        except FFmpegError as e:
            raise CuttingError(f"Falha no corte: {e}")

    def _optimize_for_platform(
        self, input_path: Path, platform: str, output_path: Path
    ) -> bool:
        """Otimiza vídeo para uma plataforma específica."""
        try:
            spec = self._config.platform_specs[platform]
            width, height = spec.resolution

            args = [
                "-i",
                str(input_path),
                "-vf",
                (
                    f"scale={width}:{height}"
                    f":force_original_aspect_ratio=increase,"
                    f"crop={width}:{height}"
                ),
                "-r",
                str(spec.fps),
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "23",
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
                logger.info("Otimizado para %s: %s", platform, output_path.name)
                return True

            return False

        except FFmpegError as e:
            logger.error("Erro na otimização para %s: %s", platform, e)
            return False

    def cleanup(self) -> None:
        """Remove arquivos temporários de corte."""
        try:
            for pattern in ["fastcut_temp_*.mp4", "temp-audio*"]:
                for file in self._config.temp_dir.glob(pattern):
                    file.unlink()
            logger.info("Arquivos temporários de corte removidos")
        except Exception as e:
            logger.warning("Erro na limpeza: %s", e)
