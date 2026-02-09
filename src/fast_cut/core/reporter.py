"""Relatórios e formatação de output do sistema."""

import logging
from datetime import timedelta

from .config import Config
from .types import ProcessingStats

logger = logging.getLogger(__name__)


class Reporter:
    """Responsável pela formatação e exibição de relatórios."""

    def __init__(self, config: Config) -> None:
        self._config = config

    def print_header(self) -> None:
        """Imprime cabeçalho do sistema."""
        from datetime import datetime

        logger.info("=" * 60)
        logger.info("SISTEMA FAST CUT - GERADOR AUTOMÁTICO DE CORTES")
        logger.info("=" * 60)
        logger.info("Iniciado em: %s", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

    def print_final_report(self, stats: ProcessingStats, duration: timedelta) -> None:
        """Imprime relatório final."""
        logger.info("=" * 60)
        logger.info("RELATÓRIO FINAL")
        logger.info("=" * 60)

        logger.info("Tempo de execução: %s", duration)
        logger.info("Vídeos baixados: %d", stats.downloaded_videos)
        logger.info("Vídeos analisados: %d", stats.analyzed_videos)
        logger.info("Total de clipes: %d", stats.generated_clips)

        logger.info("CLIPES POR PLATAFORMA:")
        for platform, count in stats.clips_by_platform.items():
            platform_name = platform.replace("_", " ").title()
            logger.info("  %s: %d clipes", platform_name, count)

        if stats.errors:
            logger.warning("ERROS (%d):", len(stats.errors))
            for error in stats.errors[:5]:
                logger.warning("  - %s", error)
            if len(stats.errors) > 5:
                logger.warning("  ... e mais %d erros", len(stats.errors) - 5)

        if stats.analyzed_videos > 0 and stats.downloaded_videos > 0:
            success_rate = (stats.analyzed_videos / stats.downloaded_videos) * 100
            logger.info("Taxa de sucesso: %.1f%%", success_rate)

        logger.info("Clipes salvos em: %s", self._config.output_dir)
        logger.info("=" * 60)

    def print_video_report(
        self,
        stats: ProcessingStats,
        duration: timedelta,
    ) -> None:
        """Imprime relatório para processamento de vídeo específico."""
        logger.info("=" * 60)
        logger.info("RESULTADO")
        logger.info("=" * 60)
        logger.info("Tempo: %s", duration)
        logger.info("Total de clipes: %d", stats.generated_clips)

        logger.info("CLIPES POR PLATAFORMA:")
        for platform, count in stats.clips_by_platform.items():
            platform_name = platform.replace("_", " ").title()
            logger.info("  %s: %d clipes", platform_name, count)

        logger.info("Clipes salvos em: %s", self._config.output_dir)
        logger.info("=" * 60)
