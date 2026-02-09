#!/usr/bin/env python3
"""Fast Cut - Sistema de Geração Automática de Cortes para Redes Sociais."""

import argparse
import logging
import sys

from fast_cut.core.config import Config
from fast_cut.utils.ffmpeg import FFmpegUtils

# Configura PATH do FFmpeg ANTES de importar serviços que dependem de pydub,
# evitando o warning "Couldn't find ffmpeg or avconv".
FFmpegUtils().setup_environment()

from fast_cut.core.system import create_system  # noqa: E402


def setup_logging(verbose: bool = False) -> None:
    """Configura o logging do sistema."""
    level = logging.DEBUG if verbose else logging.INFO

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger("fast_cut")
    root_logger.setLevel(level)
    root_logger.addHandler(handler)


def create_parser() -> argparse.ArgumentParser:
    """Cria o parser de argumentos."""
    parser = argparse.ArgumentParser(
        description="Sistema de Geração Automática de Cortes para Redes Sociais"
    )

    parser.add_argument(
        "--max-videos",
        type=int,
        default=5,
        help="Máximo de vídeos por canal (padrão: 5)",
    )

    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Pula download e usa vídeos existentes",
    )

    parser.add_argument(
        "--list-channels",
        action="store_true",
        help="Lista canais autorizados",
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Executa teste do sistema",
    )

    parser.add_argument(
        "--clear",
        action="store_true",
        help="Limpa as pastas output/ e temp/",
    )

    parser.add_argument(
        "--video",
        type=str,
        help="Processa um vídeo específico (URL do YouTube ou caminho local)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Ativa log detalhado (debug)",
    )

    parser.add_argument(
        "--no-subtitles",
        action="store_true",
        help="Desabilita geração de legendas automáticas",
    )

    return parser


def main() -> None:
    """Função principal."""
    parser = create_parser()
    args = parser.parse_args()

    setup_logging(verbose=args.verbose)

    try:
        show_header = not (args.list_channels or args.test or args.clear)

        config = Config.from_env()

        # Override de legendas via CLI
        if args.no_subtitles:
            config.subtitles_enabled = False

        # Validação apenas para comandos que precisam de canais
        if not (args.clear or args.test or args.video):
            config.validate()

        system = create_system(config=config, show_header=show_header)

        if args.clear:
            system.clear_all_outputs()
        elif args.list_channels:
            system.list_channels()
        elif args.test:
            system.test_system()
        elif args.video:
            stats = system.process_specific_video(args.video)
            sys.exit(0 if stats.generated_clips > 0 else 1)
        else:
            stats = system.run_full_pipeline(
                max_videos_per_channel=args.max_videos,
                skip_download=args.skip_download,
            )
            sys.exit(0 if stats.generated_clips > 0 else 1)

    except KeyboardInterrupt:
        print("\nExecução interrompida pelo usuário")
        sys.exit(130)
    except ValueError as e:
        logging.getLogger("fast_cut").error("Configuração inválida: %s", e)
        sys.exit(1)
    except Exception as e:
        logging.getLogger("fast_cut").error("Erro fatal: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
