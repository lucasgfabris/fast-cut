"""Gerenciamento de arquivos e diretórios."""

import logging
from pathlib import Path
from typing import List

from .config import Config

logger = logging.getLogger(__name__)

VIDEO_EXTENSIONS = [".mp4", ".mkv", ".avi", ".mov"]


class FileManager:
    """Responsável por operações de I/O: criação de diretórios, limpeza, busca."""

    def __init__(self, config: Config) -> None:
        self._config = config

    def get_existing_videos(self) -> List[Path]:
        """Obtém vídeos existentes no diretório temp."""
        if not self._config.temp_dir.exists():
            return []
        return [
            file
            for file in self._config.temp_dir.iterdir()
            if file.suffix.lower() in VIDEO_EXTENSIONS
        ]

    def cleanup_temp_videos(self) -> None:
        """Remove vídeos baixados da pasta temp após processamento."""
        try:
            removed_count = 0
            for file in self._config.temp_dir.glob("fastcut_original_*"):
                if file.is_file():
                    file.unlink()
                    removed_count += 1

            if removed_count > 0:
                logger.info(
                    "%d vídeo(s) original(is) removido(s) de temp/", removed_count
                )
        except Exception as e:
            logger.warning("Erro ao limpar vídeos temporários: %s", e)

    def clear_all_outputs(self) -> None:
        """Limpa todas as pastas de saída e temporários."""
        logger.info("Limpando diretórios")

        try:
            # Limpa output/
            if self._config.output_dir.exists():
                removed_count = 0
                for platform_dir in self._config.output_dir.iterdir():
                    if platform_dir.is_dir():
                        for file in platform_dir.iterdir():
                            if file.is_file():
                                file.unlink()
                                removed_count += 1
                logger.info("%d arquivo(s) removido(s) de output/", removed_count)

            # Limpa temp/
            if self._config.temp_dir.exists():
                removed_count = 0
                for file in self._config.temp_dir.iterdir():
                    if file.is_file():
                        file.unlink()
                        removed_count += 1
                logger.info("%d arquivo(s) removido(s) de temp/", removed_count)

            logger.info("Limpeza concluída!")
        except Exception as e:
            logger.error("Erro durante limpeza: %s", e)
