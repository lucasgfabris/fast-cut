#!/usr/bin/env python3
"""
Script para instalar FFmpeg automaticamente no Windows
"""

import os
import shutil
import sys
import zipfile
from pathlib import Path

import requests


def download_ffmpeg():
    """Baixa e instala o FFmpeg"""

    print("🔽 INSTALANDO FFMPEG")
    print("=" * 40)

    # URL do FFmpeg para Windows
    ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

    # Diretórios
    download_dir = Path("./ffmpeg_download")
    install_dir = Path("./ffmpeg")

    try:
        # Cria diretório de download
        download_dir.mkdir(exist_ok=True)

        print("📥 Baixando FFmpeg...")

        # Baixa o arquivo
        response = requests.get(ffmpeg_url, stream=True)
        zip_path = download_dir / "ffmpeg.zip"

        with open(zip_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print("📦 Extraindo FFmpeg...")

        # Extrai o arquivo
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(download_dir)

        # Encontra a pasta extraída
        extracted_folders = [
            f
            for f in download_dir.iterdir()
            if f.is_dir() and f.name.startswith("ffmpeg")
        ]

        if not extracted_folders:
            print("❌ Pasta do FFmpeg não encontrada")
            return False

        ffmpeg_folder = extracted_folders[0]
        bin_folder = ffmpeg_folder / "bin"

        # Copia os executáveis
        if install_dir.exists():
            shutil.rmtree(install_dir)

        shutil.copytree(bin_folder, install_dir)

        print("✅ FFmpeg instalado com sucesso!")
        print(f"📍 Localização: {install_dir.absolute()}")

        # Limpa arquivos de download
        shutil.rmtree(download_dir)

        # Adiciona ao PATH da sessão atual
        current_path = os.environ.get("PATH", "")
        ffmpeg_path = str(install_dir.absolute())

        if ffmpeg_path not in current_path:
            os.environ["PATH"] = ffmpeg_path + os.pathsep + current_path
            print("✅ FFmpeg adicionado ao PATH da sessão")

        # Testa a instalação
        try:
            import subprocess

            result = subprocess.run(
                [str(install_dir / "ffmpeg.exe"), "-version"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                print("🧪 Teste do FFmpeg: ✅ FUNCIONANDO")
                return True
            else:
                print("🧪 Teste do FFmpeg: ❌ FALHOU")
                return False
        except Exception as e:
            print(f"🧪 Erro no teste: {e}")
            return False

    except Exception as e:
        print(f"❌ Erro na instalação: {e}")
        return False


def main():
    """Função principal"""

    # Verifica se já está instalado
    ffmpeg_dir = Path("./ffmpeg")
    if ffmpeg_dir.exists() and (ffmpeg_dir / "ffmpeg.exe").exists():
        print("✅ FFmpeg já está instalado!")

        # Adiciona ao PATH
        current_path = os.environ.get("PATH", "")
        ffmpeg_path = str(ffmpeg_dir.absolute())

        if ffmpeg_path not in current_path:
            os.environ["PATH"] = ffmpeg_path + os.pathsep + current_path
            print("✅ FFmpeg adicionado ao PATH da sessão")

        return True

    # Instala o FFmpeg
    success = download_ffmpeg()

    if success:
        print("\n🎉 INSTALAÇÃO CONCLUÍDA!")
        print("Agora você pode executar:")
        print("  python main.py --max-videos 1")
    else:
        print("\n❌ INSTALAÇÃO FALHADA")
        print("Instale o FFmpeg manualmente:")
        print("1. Baixe de: https://ffmpeg.org/download.html")
        print("2. Extraia para uma pasta")
        print("3. Adicione ao PATH do Windows")

    return success


if __name__ == "__main__":
    main()
