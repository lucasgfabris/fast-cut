"""Utilitários para FFmpeg."""

import os
import subprocess
from pathlib import Path
from typing import List, Optional


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
        local_ffmpeg = Path.cwd() / "ffmpeg" / "ffmpeg.exe"
        if local_ffmpeg.exists():
            return local_ffmpeg

        # Verifica FFmpeg no PATH
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                check=True,
                timeout=5,
            )
            if result.returncode == 0:
                return Path("ffmpeg")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
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
