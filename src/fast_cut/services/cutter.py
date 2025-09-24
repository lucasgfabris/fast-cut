"""Serviço de corte de vídeos."""

from pathlib import Path
from typing import List

from ..core.config import Config
from ..core.types import Clip, ProcessingResults
from ..utils.ffmpeg import FFmpegError, FFmpegUtils


class CuttingError(Exception):
    """Erro específico de corte."""

    pass


class VideoCutter:
    """Serviço responsável pelo corte e otimização de vídeos."""

    def __init__(self) -> None:
        self._ffmpeg = FFmpegUtils()
        Config.create_directories()

    def process_clips(self, clips: List[Clip], source_video: Path) -> ProcessingResults:
        """Processa uma lista de clipes para todas as plataformas."""
        if not self._ffmpeg.is_available:
            raise CuttingError("FFmpeg não está disponível")

        results = {platform: [] for platform in Config.PLATFORM_SPECS}
        video_name = source_video.stem

        for i, clip in enumerate(clips, 1):
            print(f"✂️  Processando clipe {i}/{len(clips)}")

            temp_clip = Config.TEMP_DIR / f"{video_name}_clip_{i}_temp.mp4"

            try:
                # Corta o clipe
                self._cut_clip(source_video, clip, temp_clip)

                # Otimiza para cada plataforma
                for platform in Config.PLATFORM_SPECS:
                    platform_dir = Config.OUTPUT_DIR / platform
                    output_path = platform_dir / f"{video_name}_clip_{i}_{platform}.mp4"

                    if self._optimize_for_platform(temp_clip, platform, output_path):
                        results[platform].append(str(output_path))

            except Exception as e:
                print(f"❌ Erro no clipe {i}: {e}")
            finally:
                temp_clip.unlink(missing_ok=True)

        return results

    def _cut_clip(self, video_path: Path, clip: Clip, output_path: Path) -> None:
        """Corta um clipe do vídeo."""
        args = [
            "-i", str(video_path),
            "-ss", str(clip.start_time),
            "-t", str(clip.duration),
            "-c:v", "libx264",
            "-c:a", "aac",
            "-preset", "fast",
            "-crf", "23",
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
            spec = Config.PLATFORM_SPECS[platform]
            width, height = spec.resolution

            args = [
                "-i", str(input_path),
                "-vf", f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}",
                "-r", str(spec.fps),
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", Config.AUDIO_BITRATE,
                "-movflags", "+faststart",
                "-y",
                str(output_path),
            ]

            self._ffmpeg.run_command(args)

            if output_path.exists():
                print(f"✅ Otimizado para {platform}: {output_path.name}")
                return True

            return False

        except FFmpegError as e:
            print(f"❌ Erro na otimização para {platform}: {e}")
            return False

    def cleanup(self) -> None:
        """Remove arquivos temporários de corte."""
        try:
            for pattern in ["*_temp.mp4", "temp-audio*"]:
                for file in Config.TEMP_DIR.glob(pattern):
                    file.unlink()
            print("🧹 Arquivos temporários de corte removidos")
        except Exception as e:
            print(f"⚠️  Erro na limpeza: {e}")
