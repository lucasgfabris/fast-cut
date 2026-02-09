"""Configurações do sistema."""

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


@dataclass
class PlatformSpec:
    """Especificações de uma plataforma de vídeo."""

    resolution: tuple[int, int]
    fps: int
    format: str
    max_duration: int


# Plataformas padrão (podem ser estendidas via Config)
DEFAULT_PLATFORM_SPECS: Dict[str, PlatformSpec] = {
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


@dataclass
class Config:
    """Configurações centralizadas do sistema (instanciável e injetável)."""

    # Canais autorizados
    authorized_channels: List[str] = field(default_factory=list)

    # Diretórios
    output_dir: Path = field(default_factory=lambda: Path("./output"))
    temp_dir: Path = field(default_factory=lambda: Path("./temp"))

    # Configurações de corte
    min_clip_duration: int = 15
    max_clip_duration: int = 60
    clips_per_video: int = 3

    # Configurações de qualidade
    video_quality: str = "1080p"
    audio_bitrate: str = "128k"

    # Configurações de análise
    energy_threshold: float = 0.7
    silence_threshold: int = -40

    # Especificações das plataformas
    platform_specs: Dict[str, PlatformSpec] = field(
        default_factory=lambda: dict(DEFAULT_PLATFORM_SPECS)
    )

    @classmethod
    def from_env(cls, env_path: str | None = None) -> "Config":
        """Cria Config a partir de variáveis de ambiente / .env."""
        from dotenv import load_dotenv

        load_dotenv(env_path)

        channels_raw = os.getenv("AUTHORIZED_CHANNELS", "")
        channels = [
            ch.strip() for ch in channels_raw.split(",") if ch.strip()
        ]

        # Carrega plataformas de JSON externo se configurado
        platforms_file = os.getenv("PLATFORMS_FILE", "")
        if platforms_file:
            platform_specs = cls.load_platforms_from_file(
                Path(platforms_file)
            )
        else:
            platform_specs = dict(DEFAULT_PLATFORM_SPECS)

        return cls(
            authorized_channels=channels,
            output_dir=Path(os.getenv("OUTPUT_DIR", "./output")),
            temp_dir=Path(os.getenv("TEMP_DIR", "./temp")),
            min_clip_duration=int(os.getenv("MIN_CLIP_DURATION", "15")),
            max_clip_duration=int(os.getenv("MAX_CLIP_DURATION", "60")),
            clips_per_video=int(os.getenv("CLIPS_PER_VIDEO", "3")),
            video_quality=os.getenv("VIDEO_QUALITY", "1080p"),
            audio_bitrate=os.getenv("AUDIO_BITRATE", "128k"),
            energy_threshold=float(os.getenv("ENERGY_THRESHOLD", "0.7")),
            silence_threshold=int(os.getenv("SILENCE_THRESHOLD", "-40")),
            platform_specs=platform_specs,
        )

    @staticmethod
    def load_platforms_from_file(
        path: Path,
    ) -> Dict[str, "PlatformSpec"]:
        """Carrega especificações de plataformas de um arquivo JSON.

        Formato esperado:
        {
            "nome_plataforma": {
                "resolution": [1080, 1920],
                "fps": 30,
                "format": "mp4",
                "max_duration": 60
            }
        }
        """
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            specs: Dict[str, PlatformSpec] = {}

            for name, spec_data in data.items():
                specs[name] = PlatformSpec(
                    resolution=tuple(spec_data["resolution"]),
                    fps=spec_data["fps"],
                    format=spec_data["format"],
                    max_duration=spec_data["max_duration"],
                )

            logger.info(
                "Plataformas carregadas de %s: %s",
                path,
                list(specs.keys()),
            )
            return specs

        except Exception as e:
            logger.warning(
                "Erro ao carregar plataformas de %s: %s. Usando padrão.",
                path,
                e,
            )
            return dict(DEFAULT_PLATFORM_SPECS)

    def create_directories(self) -> None:
        """Cria os diretórios necessários."""
        self.output_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)

        for platform in self.platform_specs:
            platform_dir = self.output_dir / platform
            platform_dir.mkdir(exist_ok=True)

    def validate(self) -> None:
        """Valida as configurações. Levanta ValueError se inválida."""
        if not self.authorized_channels:
            raise ValueError(
                "Nenhum canal autorizado configurado. "
                "Configure AUTHORIZED_CHANNELS no arquivo .env"
            )

        if self.min_clip_duration >= self.max_clip_duration:
            raise ValueError(
                "MIN_CLIP_DURATION deve ser menor que MAX_CLIP_DURATION"
            )

        logger.info(
            "Configuração validada: %d canais, duração %ds-%ds, %d clipes/vídeo",
            len(self.authorized_channels),
            self.min_clip_duration,
            self.max_clip_duration,
            self.clips_per_video,
        )
