"""Testes para tipos e estruturas de dados."""

from pathlib import Path

from fast_cut.core.types import Clip, ProcessingStats


class TestClip:
    """Testes para o dataclass Clip."""

    def test_valid_clip(self) -> None:
        """Clip com valores válidos deve ser is_valid."""
        clip = Clip(
            start_time=10.0,
            end_time=25.0,
            duration=15.0,
            score=0.8,
            source_video=Path("video.mp4"),
        )
        assert clip.is_valid

    def test_invalid_clip_zero_duration(self) -> None:
        """Clip com duração zero não é válido."""
        clip = Clip(
            start_time=10.0,
            end_time=10.0,
            duration=0.0,
            score=0.5,
            source_video=Path("video.mp4"),
        )
        assert not clip.is_valid

    def test_invalid_clip_negative_duration(self) -> None:
        """Clip com start > end não é válido."""
        clip = Clip(
            start_time=25.0,
            end_time=10.0,
            duration=-15.0,
            score=0.5,
            source_video=Path("video.mp4"),
        )
        assert not clip.is_valid


class TestProcessingStats:
    """Testes para ProcessingStats."""

    def test_default_values(self) -> None:
        """Valores padrão devem ser sensatos."""
        stats = ProcessingStats()
        assert stats.downloaded_videos == 0
        assert stats.analyzed_videos == 0
        assert stats.generated_clips == 0
        assert stats.clips_by_platform == {}
        assert stats.errors == []

    def test_errors_are_independent(self) -> None:
        """Cada instância deve ter sua própria lista de erros."""
        stats1 = ProcessingStats()
        stats2 = ProcessingStats()
        stats1.errors.append("erro1")
        assert stats2.errors == []

    def test_clips_by_platform_independent(self) -> None:
        """Cada instância deve ter seu próprio dict."""
        stats1 = ProcessingStats()
        stats2 = ProcessingStats()
        stats1.clips_by_platform["yt"] = 5
        assert stats2.clips_by_platform == {}
