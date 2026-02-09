#!/usr/bin/env python3
"""Script de configuração inicial do projeto."""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Executa um comando."""
    print(f"🔧 {description}...")

    try:
        subprocess.run(cmd, check=True)
        print(f"✅ {description} - Concluído")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Falhou: {e}")
        return False
    except FileNotFoundError:
        print(f"⚠️  {description} - Comando não encontrado")
        return False


def main() -> int:
    """Configura o projeto."""
    print("🚀 Configurando projeto Fast Cut...")
    print("=" * 40)

    project_root = Path(__file__).parent.parent
    original_cwd = Path.cwd()

    try:
        import os

        os.chdir(project_root)

        steps = [
            (["pip", "install", "-e", ".[dev]"], "Instalando dependências"),
            (["pre-commit", "install"], "Configurando pre-commit hooks"),
        ]

        for cmd, description in steps:
            if not run_command(cmd, description):
                print(f"\n❌ Falha na configuração: {description}")
                return 1

        print("\n🎉 Configuração concluída!")
        print("\nPróximos passos:")
        print("1. Copie .env.example para .env e configure")
        print("2. Execute: npm run start:test")
        print("3. Execute: npm run check  # Para validar código")

        return 0

    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    sys.exit(main())
