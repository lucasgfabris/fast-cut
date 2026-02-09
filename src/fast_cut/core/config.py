"""Configurações do sistema."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv()


@dataclass
class PlatformSpec:
    """Especificações de uma plataforma de vídeo."""

    resolution: tuple[int, int]
    fps: int
    format: str
    max_duration: int


class Config:
    """Configurações centralizadas do sistema."""

    # Canais autorizados
    AUTHORIZED_CHANNELS: List[str] = [
        channel.strip()
        for channel in os.getenv("AUTHORIZED_CHANNELS", "").split(",")
        if channel.strip()
    ]

    # Diretórios
    OUTPUT_DIR: Path = Path(os.getenv("OUTPUT_DIR", "./output"))
    TEMP_DIR: Path = Path(os.getenv("TEMP_DIR", "./temp"))

    # Configurações de corte
    MIN_CLIP_DURATION: int = int(os.getenv("MIN_CLIP_DURATION", "15"))
    MAX_CLIP_DURATION: int = int(os.getenv("MAX_CLIP_DURATION", "60"))
    CLIPS_PER_VIDEO: int = int(os.getenv("CLIPS_PER_VIDEO", "3"))

    # Configurações de qualidade
    VIDEO_QUALITY: str = os.getenv("VIDEO_QUALITY", "1080p")
    AUDIO_BITRATE: str = os.getenv("AUDIO_BITRATE", "128k")

    # Configurações de análise
    ENERGY_THRESHOLD: float = float(os.getenv("ENERGY_THRESHOLD", "0.7"))
    SILENCE_THRESHOLD: int = int(os.getenv("SILENCE_THRESHOLD", "-40"))

    # Especificações das plataformas
    PLATFORM_SPECS: Dict[str, PlatformSpec] = {
        "youtube_shorts": PlatformSpec(
            resolution=(1080, 1920), fps=30, format="mp4", max_duration=60
        ),
        "tiktok": PlatformSpec(
            resolution=(1080, 1920), fps=30, format="mp4", max_duration=60
        ),
        "instagram_reels": PlatformSpec(
            resolution=(1080, 1920), fps=30, format="mp4", max_duration=60
        ),
    }

    @classmethod
    def create_directories(cls) -> None:
        """Cria os diretórios necessários."""
        cls.OUTPUT_DIR.mkdir(exist_ok=True)
        cls.TEMP_DIR.mkdir(exist_ok=True)

        for platform in cls.PLATFORM_SPECS:
            platform_dir = cls.OUTPUT_DIR / platform
            platform_dir.mkdir(exist_ok=True)

    @classmethod
    def validate(cls) -> None:
        """Valida as configurações."""
        if not cls.AUTHORIZED_CHANNELS:
            raise ValueError(
                "Nenhum canal autorizado configurado. "
                "Configure AUTHORIZED_CHANNELS no arquivo .env"
            )

        if cls.MIN_CLIP_DURATION >= cls.MAX_CLIP_DURATION:
            raise ValueError("MIN_CLIP_DURATION deve ser menor que MAX_CLIP_DURATION")

        print("✅ Configuração validada:")
        print(f"   Canais: {len(cls.AUTHORIZED_CHANNELS)}")
        print(f"   Duração dos clipes: {cls.MIN_CLIP_DURATION}s-{cls.MAX_CLIP_DURATION}s")
        print(f"   Clipes por vídeo: {cls.CLIPS_PER_VIDEO}")
