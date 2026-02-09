#!/usr/bin/env python3
"""Script para instalar FFmpeg automaticamente no Windows."""

import os
import shutil
import subprocess
import zipfile
from pathlib import Path

import requests  # type: ignore[import-untyped]


def download_ffmpeg() -> bool:
    """Baixa e instala o FFmpeg."""
    print("INSTALANDO FFMPEG")
    print("=" * 40)

    ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/" "ffmpeg-release-essentials.zip"

    download_dir = Path("./ffmpeg_download")
    install_dir = Path("./ffmpeg")

    try:
        download_dir.mkdir(exist_ok=True)

        print("Baixando FFmpeg...")

        response = requests.get(ffmpeg_url, stream=True)
        zip_path = download_dir / "ffmpeg.zip"

        with open(zip_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print("Extraindo FFmpeg...")

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(download_dir)

        extracted_folders = [
            f
            for f in download_dir.iterdir()
            if f.is_dir() and f.name.startswith("ffmpeg")
        ]

        if not extracted_folders:
            print("Pasta do FFmpeg não encontrada")
            return False

        ffmpeg_folder = extracted_folders[0]
        bin_folder = ffmpeg_folder / "bin"

        if install_dir.exists():
            shutil.rmtree(install_dir)

        shutil.copytree(bin_folder, install_dir)

        print(f"FFmpeg instalado em: {install_dir.absolute()}")

        shutil.rmtree(download_dir)

        current_path = os.environ.get("PATH", "")
        ffmpeg_path = str(install_dir.absolute())

        if ffmpeg_path not in current_path:
            os.environ["PATH"] = ffmpeg_path + os.pathsep + current_path

        try:
            result = subprocess.run(
                [str(install_dir / "ffmpeg.exe"), "-version"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                print("Teste do FFmpeg: OK")
                return True
            else:
                print("Teste do FFmpeg: FALHOU")
                return False
        except Exception as e:
            print(f"Erro no teste: {e}")
            return False

    except Exception as e:
        print(f"Erro na instalação: {e}")
        return False


def main() -> bool:
    """Função principal."""
    ffmpeg_dir = Path("./ffmpeg")
    if ffmpeg_dir.exists() and (ffmpeg_dir / "ffmpeg.exe").exists():
        print("FFmpeg já está instalado!")

        current_path = os.environ.get("PATH", "")
        ffmpeg_path = str(ffmpeg_dir.absolute())

        if ffmpeg_path not in current_path:
            os.environ["PATH"] = ffmpeg_path + os.pathsep + current_path

        return True

    success = download_ffmpeg()

    if success:
        print("\nINSTALAÇÃO CONCLUÍDA!")
        print("Agora você pode executar:")
        print("  python main.py --max-videos 1")
    else:
        print("\nINSTALAÇÃO FALHADA")
        print("Instale o FFmpeg manualmente:")
        print("1. Baixe de: https://ffmpeg.org/download.html")
        print("2. Extraia para uma pasta")
        print("3. Adicione ao PATH do Windows")

    return success


if __name__ == "__main__":
    main()
