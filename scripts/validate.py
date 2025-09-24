#!/usr/bin/env python3
"""Script de validação para garantir qualidade do código."""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Executa um comando e retorna se foi bem-sucedido."""
    print(f"🔍 {description}...")
    
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True
        )
        print(f"✅ {description} - OK")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FALHOU")
        if e.stdout:
            print(f"STDOUT:\n{e.stdout}")
        if e.stderr:
            print(f"STDERR:\n{e.stderr}")
        return False
    except FileNotFoundError:
        print(f"⚠️  {description} - Ferramenta não encontrada")
        return False


def main() -> int:
    """Executa todas as validações."""
    print("🚀 Executando validações de qualidade do código...")
    print("=" * 50)
    
    # Muda para o diretório raiz do projeto
    project_root = Path(__file__).parent.parent
    original_cwd = Path.cwd()
    
    try:
        import os
        os.chdir(project_root)
        
        validations = [
            (["black", "--check", "."], "Verificação de formatação (Black)"),
            (["isort", "--check-only", "."], "Verificação de imports (isort)"),
            (["flake8", "."], "Linting (Flake8)"),
            (["mypy", "."], "Verificação de tipos (MyPy)"),
        ]
        
        results = []
        for cmd, description in validations:
            success = run_command(cmd, description)
            results.append(success)
        
        print("\n" + "=" * 50)
        
        if all(results):
            print("🎉 Todas as validações passaram!")
            return 0
        else:
            failed = sum(1 for r in results if not r)
            print(f"💥 {failed} validação(ões) falharam!")
            print("\nPara corrigir automaticamente:")
            print("  make format  # Corrige formatação")
            print("  make lint    # Mostra problemas de linting")
            print("  make type-check  # Mostra problemas de tipos")
            return 1
            
    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    sys.exit(main())
