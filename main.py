#!/usr/bin/env python3
"""Fast Cut - Sistema de Geração Automática de Cortes para Redes Sociais."""

import argparse
import sys
from pathlib import Path

# Adiciona src ao path para imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fast_cut.core.system import FastCutSystem


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

    return parser


def main() -> None:
    """Função principal."""
    parser = create_parser()
    args = parser.parse_args()

    try:
        # Para comandos simples, não mostra o cabeçalho completo
        show_header = not (args.list_channels or args.test or args.clear)
        system = FastCutSystem(show_header=show_header)

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

            # Código de saída baseado no sucesso
            sys.exit(0 if stats.generated_clips > 0 else 1)

    except KeyboardInterrupt:
        print("\n⏹️  Execução interrompida pelo usuário")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()