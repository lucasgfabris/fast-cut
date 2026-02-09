"""Fixtures compartilhadas para todos os testes."""

import tempfile
from pathlib import Path

import pytest

from fast_cut.core.config import Config, PlatformSpec


@pytest.fixture
def tmp_dirs(tmp_path: Path) -> tuple[Path, Path]:
    """Cria diretórios temporários para output e temp."""
    output_dir = tmp_path / "output"
    temp_dir = tmp_path / "temp"
    output_dir.mkdir()
    temp_dir.mkdir()
    return output_dir, temp_dir


@pytest.fixture
def test_config(tmp_dirs: tuple[Path, Path]) -> Config:
    """Config de teste com diretórios temporários e valores padrão."""
    output_dir, temp_dir = tmp_dirs
    return Config(
        authorized_channels=["UCtest1", "UCtest2"],
        output_dir=output_dir,
        temp_dir=temp_dir,
        min_clip_duration=10,
        max_clip_duration=30,
        clips_per_video=2,
        video_quality="720p",
        audio_bitrate="128k",
        energy_threshold=0.5,
        silence_threshold=-40,
        platform_specs={
            "youtube_shorts": PlatformSpec(
                resolution=(1080, 1920), fps=30, format="mp4", max_duration=60
            ),
            "tiktok": PlatformSpec(
                resolution=(1080, 1920), fps=30, format="mp4", max_duration=60
            ),
        },
    )


@pytest.fixture
def minimal_config(tmp_dirs: tuple[Path, Path]) -> Config:
    """Config mínima sem canais (para testes de validação)."""
    output_dir, temp_dir = tmp_dirs
    return Config(
        authorized_channels=[],
        output_dir=output_dir,
        temp_dir=temp_dir,
    )
