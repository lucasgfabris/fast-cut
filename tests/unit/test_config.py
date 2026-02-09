"""Testes para o módulo de configuração."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from fast_cut.core.config import Config, PlatformSpec


class TestConfigCreation:
    """Testes de criação da Config."""

    def test_default_config(self) -> None:
        """Config padrão deve ter valores sensatos."""
        config = Config()
        assert config.min_clip_duration == 15
        assert config.max_clip_duration == 60
        assert config.clips_per_video == 3
        assert config.energy_threshold == 0.7
        assert config.silence_threshold == -40
        assert config.audio_bitrate == "128k"
        assert len(config.platform_specs) == 3

    def test_custom_config(self) -> None:
        """Config customizada deve aceitar valores."""
        config = Config(
            authorized_channels=["ch1", "ch2"],
            min_clip_duration=20,
            max_clip_duration=45,
        )
        assert config.authorized_channels == ["ch1", "ch2"]
        assert config.min_clip_duration == 20
        assert config.max_clip_duration == 45

    def test_from_env(self) -> None:
        """Config.from_env deve ler variáveis de ambiente."""
        env_vars = {
            "AUTHORIZED_CHANNELS": "ch1, ch2, ch3",
            "OUTPUT_DIR": "/tmp/out",
            "TEMP_DIR": "/tmp/temp",
            "MIN_CLIP_DURATION": "20",
            "MAX_CLIP_DURATION": "45",
            "CLIPS_PER_VIDEO": "5",
            "ENERGY_THRESHOLD": "0.8",
            "SILENCE_THRESHOLD": "-30",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = Config.from_env()

        assert config.authorized_channels == ["ch1", "ch2", "ch3"]
        assert config.output_dir == Path("/tmp/out")
        assert config.temp_dir == Path("/tmp/temp")
        assert config.min_clip_duration == 20
        assert config.max_clip_duration == 45
        assert config.clips_per_video == 5
        assert config.energy_threshold == 0.8
        assert config.silence_threshold == -30

    def test_from_env_defaults(self) -> None:
        """Config.from_env com variáveis vazias usa defaults."""
        with patch("dotenv.load_dotenv"):
            with patch.dict(os.environ, {}, clear=True):
                config = Config.from_env()

        assert config.authorized_channels == []
        assert config.min_clip_duration == 15
        assert config.max_clip_duration == 60


class TestConfigValidation:
    """Testes de validação da Config."""

    def test_valid_config(self, test_config: Config) -> None:
        """Config válida não deve levantar exceção."""
        test_config.validate()  # Não deve levantar

    def test_no_channels_raises(self, minimal_config: Config) -> None:
        """Config sem canais deve levantar ValueError."""
        with pytest.raises(ValueError, match="Nenhum canal autorizado"):
            minimal_config.validate()

    def test_invalid_duration_raises(self, test_config: Config) -> None:
        """min >= max deve levantar ValueError."""
        test_config.min_clip_duration = 60
        test_config.max_clip_duration = 30

        with pytest.raises(ValueError, match="MIN_CLIP_DURATION deve ser menor"):
            test_config.validate()

    def test_equal_duration_raises(self, test_config: Config) -> None:
        """min == max deve levantar ValueError."""
        test_config.min_clip_duration = 30
        test_config.max_clip_duration = 30

        with pytest.raises(ValueError):
            test_config.validate()


class TestConfigDirectories:
    """Testes de criação de diretórios."""

    def test_create_directories(self, test_config: Config) -> None:
        """Deve criar diretórios de output e plataformas."""
        test_config.create_directories()

        assert test_config.output_dir.exists()
        assert test_config.temp_dir.exists()

        for platform in test_config.platform_specs:
            assert (test_config.output_dir / platform).exists()

    def test_create_directories_idempotent(self, test_config: Config) -> None:
        """Chamar create_directories múltiplas vezes não deve falhar."""
        test_config.create_directories()
        test_config.create_directories()  # Não deve levantar


class TestPlatformSpec:
    """Testes da PlatformSpec."""

    def test_platform_spec_creation(self) -> None:
        """PlatformSpec deve ser criável com os campos corretos."""
        spec = PlatformSpec(
            resolution=(1080, 1920), fps=30, format="mp4", max_duration=60
        )
        assert spec.resolution == (1080, 1920)
        assert spec.fps == 30
        assert spec.format == "mp4"
        assert spec.max_duration == 60

    def test_custom_platform_specs(self) -> None:
        """Config deve aceitar platform_specs customizadas."""
        custom_specs = {
            "custom_platform": PlatformSpec(
                resolution=(720, 1280),
                fps=24,
                format="webm",
                max_duration=120,
            )
        }
        config = Config(platform_specs=custom_specs)
        assert "custom_platform" in config.platform_specs
        assert config.platform_specs["custom_platform"].fps == 24

    def test_load_platforms_from_json_file(self, tmp_path: Path) -> None:
        """Deve carregar plataformas de um arquivo JSON."""
        import json

        platforms_data = {
            "twitter_video": {
                "resolution": [1280, 720],
                "fps": 30,
                "format": "mp4",
                "max_duration": 140,
            },
            "custom": {
                "resolution": [720, 1280],
                "fps": 24,
                "format": "webm",
                "max_duration": 90,
            },
        }

        json_path = tmp_path / "platforms.json"
        json_path.write_text(json.dumps(platforms_data), encoding="utf-8")

        specs = Config.load_platforms_from_file(json_path)

        assert "twitter_video" in specs
        assert "custom" in specs
        assert specs["twitter_video"].resolution == (1280, 720)
        assert specs["custom"].fps == 24
        assert specs["custom"].max_duration == 90

    def test_load_platforms_invalid_file_falls_back(self, tmp_path: Path) -> None:
        """Arquivo inválido deve retornar plataformas padrão."""
        bad_path = tmp_path / "naoexiste.json"
        specs = Config.load_platforms_from_file(bad_path)

        # Deve retornar os defaults
        assert "youtube_shorts" in specs
        assert "tiktok" in specs
        assert "instagram_reels" in specs
