"""Utilitários para FFmpeg."""

import logging
import os
import platform
import subprocess
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


def _ffmpeg_binary_name() -> str:
    """Retorna o nome do executável do FFmpeg conforme o SO."""
    return "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"


def _ffprobe_binary_name() -> str:
    """Retorna o nome do executável do FFprobe conforme o SO."""
    return "ffprobe.exe" if platform.system() == "Windows" else "ffprobe"


class FFmpegError(Exception):
    """Erro específico do FFmpeg."""

    pass


class FFmpegUtils:
    """Utilitários para operações com FFmpeg."""

    def __init__(self) -> None:
        self._ffmpeg_path = self._find_ffmpeg()

    def _find_ffmpeg(self) -> Optional[Path]:
        """Localiza o executável do FFmpeg."""
        # Verifica FFmpeg local primeiro
        local_ffmpeg = Path.cwd() / "ffmpeg" / _ffmpeg_binary_name()
        if local_ffmpeg.exists():
            return local_ffmpeg

        # Verifica FFmpeg no PATH
        try:
            result = subprocess.run(
                [_ffmpeg_binary_name(), "-version"],
                capture_output=True,
                check=True,
                timeout=5,
            )
            if result.returncode == 0:
                return Path(_ffmpeg_binary_name())
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ):
            pass

        return None

    @property
    def is_available(self) -> bool:
        """Verifica se FFmpeg está disponível."""
        return self._ffmpeg_path is not None

    def run_command(self, args: List[str]) -> subprocess.CompletedProcess:
        """Executa um comando FFmpeg."""
        if not self.is_available:
            raise FFmpegError("FFmpeg não está disponível")

        cmd = [str(self._ffmpeg_path)] + args

        try:
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=300,  # 5 minutos timeout
            )
        except subprocess.CalledProcessError as e:
            raise FFmpegError(f"Comando FFmpeg falhou: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise FFmpegError("Comando FFmpeg expirou")

    def setup_environment(self) -> None:
        """Configura o ambiente para usar FFmpeg local."""
        ffmpeg_dir = Path.cwd() / "ffmpeg"
        if ffmpeg_dir.exists():
            current_path = os.environ.get("PATH", "")
            if str(ffmpeg_dir) not in current_path:
                os.environ["PATH"] = f"{ffmpeg_dir}{os.pathsep}{current_path}"

    @staticmethod
    def get_local_ffmpeg_path() -> Optional[Path]:
        """Retorna o caminho do FFmpeg local se existir."""
        ffmpeg_dir = Path.cwd() / "ffmpeg"
        ffmpeg_path = ffmpeg_dir / _ffmpeg_binary_name()
        if ffmpeg_path.exists():
            return ffmpeg_path
        return None

    @staticmethod
    def get_local_ffprobe_path() -> Optional[Path]:
        """Retorna o caminho do FFprobe local se existir."""
        ffmpeg_dir = Path.cwd() / "ffmpeg"
        ffprobe_path = ffmpeg_dir / _ffprobe_binary_name()
        if ffprobe_path.exists():
            return ffprobe_path
        return None
