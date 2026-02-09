"""Testes para o FileManager."""

from pathlib import Path

from fast_cut.core.config import Config
from fast_cut.core.file_manager import FileManager


class TestGetExistingVideos:
    """Testes para busca de vídeos existentes."""

    def test_empty_temp_dir(self, test_config: Config) -> None:
        """Retorna lista vazia se não há vídeos."""
        fm = FileManager(test_config)
        assert fm.get_existing_videos() == []

    def test_finds_video_files(self, test_config: Config) -> None:
        """Deve encontrar arquivos de vídeo no temp."""
        # Cria arquivos fake
        (test_config.temp_dir / "video1.mp4").touch()
        (test_config.temp_dir / "video2.mkv").touch()
        (test_config.temp_dir / "nota.txt").touch()

        fm = FileManager(test_config)
        videos = fm.get_existing_videos()

        assert len(videos) == 2
        names = {v.name for v in videos}
        assert "video1.mp4" in names
        assert "video2.mkv" in names
        assert "nota.txt" not in names

    def test_nonexistent_temp_dir(self, tmp_path: Path) -> None:
        """Retorna vazio se o diretório temp não existe."""
        config = Config(temp_dir=tmp_path / "naoexiste")
        fm = FileManager(config)
        assert fm.get_existing_videos() == []


class TestCleanupTempVideos:
    """Testes para limpeza de vídeos temporários."""

    def test_removes_fastcut_originals(self, test_config: Config) -> None:
        """Deve remover apenas arquivos fastcut_original_*."""
        (test_config.temp_dir / "fastcut_original_abc.mp4").touch()
        (test_config.temp_dir / "fastcut_original_def.mkv").touch()
        (test_config.temp_dir / "other_video.mp4").touch()

        fm = FileManager(test_config)
        fm.cleanup_temp_videos()

        remaining = list(test_config.temp_dir.iterdir())
        assert len(remaining) == 1
        assert remaining[0].name == "other_video.mp4"

    def test_no_files_to_clean(self, test_config: Config) -> None:
        """Não deve falhar se não há arquivos para limpar."""
        fm = FileManager(test_config)
        fm.cleanup_temp_videos()  # Não deve levantar


class TestClearAllOutputs:
    """Testes para limpeza completa."""

    def test_clears_output_and_temp(self, test_config: Config) -> None:
        """Deve limpar arquivos em output/ e temp/."""
        test_config.create_directories()

        # Cria arquivos fake
        for platform in test_config.platform_specs:
            (test_config.output_dir / platform / "clip.mp4").touch()
        (test_config.temp_dir / "temp_file.mp4").touch()

        fm = FileManager(test_config)
        fm.clear_all_outputs()

        # Verifica que output está vazio
        for platform in test_config.platform_specs:
            files = list((test_config.output_dir / platform).iterdir())
            assert len(files) == 0

        # Verifica que temp está vazio
        temp_files = list(test_config.temp_dir.iterdir())
        assert len(temp_files) == 0
