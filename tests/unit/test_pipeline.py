"""Testes para o PipelineOrchestrator."""

from pathlib import Path
from typing import List, Optional
from unittest.mock import MagicMock

import pytest

from fast_cut.core.config import Config
from fast_cut.core.file_manager import FileManager
from fast_cut.core.pipeline import PipelineOrchestrator
from fast_cut.core.types import Clip, ProcessingResults, VideoMetadata

# -- Fakes para testes --------------------------------------------------------


class FakeDownloader:
    """Implementação fake do Downloader."""

    def __init__(self, videos_to_return: List[Path] | None = None) -> None:
        self._videos = videos_to_return or []
        self.cleanup_called = False

    def download_from_channels(self, max_per_channel: int = 5) -> List[Path]:
        return self._videos

    def download_video(self, video: VideoMetadata) -> Optional[Path]:
        return self._videos[0] if self._videos else None

    def get_channel_videos(
        self, channel_id: str, max_videos: int = 10
    ) -> List[VideoMetadata]:
        return []

    def cleanup(self) -> None:
        self.cleanup_called = True


class FakeAnalyzer:
    """Implementação fake do Analyzer."""

    def __init__(self, clips: List[Clip] | None = None) -> None:
        self._clips = clips or []

    def find_best_clips(self, video_path: Path) -> List[Clip]:
        return self._clips


class FakeCutter:
    """Implementação fake do Cutter."""

    def __init__(self, results: ProcessingResults | None = None) -> None:
        self._results = results or {}
        self.cleanup_called = False

    def process_clips(
        self,
        clips: List[Clip],
        source_video: Path,
        video_num: int = 1,
        total_videos: int = 1,
    ) -> ProcessingResults:
        return self._results

    def cleanup(self) -> None:
        self.cleanup_called = True


# -- Testes -------------------------------------------------------------------


class TestPipelineNoVideos:
    """Testes quando não há vídeos disponíveis."""

    def test_run_no_videos_returns_empty_stats(self, test_config: Config) -> None:
        """Pipeline sem vídeos retorna stats vazias."""
        pipeline = PipelineOrchestrator(
            config=test_config,
            downloader=FakeDownloader([]),
            analyzer=FakeAnalyzer(),
            cutter=FakeCutter(),
            file_manager=FileManager(test_config),
        )

        stats = pipeline.run()
        assert stats.downloaded_videos == 0
        assert stats.generated_clips == 0


class TestPipelineWithVideos:
    """Testes do pipeline com vídeos disponíveis."""

    def test_run_processes_videos(self, test_config: Config) -> None:
        """Pipeline deve processar vídeos e gerar clips."""
        video = test_config.temp_dir / "video.mp4"
        video.touch()

        clips = [
            Clip(
                start_time=0,
                end_time=15,
                duration=15,
                score=0.9,
                source_video=video,
            )
        ]
        results: ProcessingResults = {
            "youtube_shorts": ["/out/clip1.mp4"],
            "tiktok": ["/out/clip2.mp4"],
        }

        pipeline = PipelineOrchestrator(
            config=test_config,
            downloader=FakeDownloader([video]),
            analyzer=FakeAnalyzer(clips),
            cutter=FakeCutter(results),
            file_manager=FileManager(test_config),
        )

        stats = pipeline.run()

        assert stats.downloaded_videos == 1
        assert stats.analyzed_videos == 1
        assert stats.generated_clips == 2

    def test_cleanup_called(self, test_config: Config) -> None:
        """Pipeline deve chamar cleanup dos serviços."""
        video = test_config.temp_dir / "video.mp4"
        video.touch()

        clips = [
            Clip(
                start_time=0,
                end_time=15,
                duration=15,
                score=0.9,
                source_video=video,
            )
        ]

        downloader = FakeDownloader([video])
        cutter = FakeCutter({"youtube_shorts": [], "tiktok": []})

        pipeline = PipelineOrchestrator(
            config=test_config,
            downloader=downloader,
            analyzer=FakeAnalyzer(clips),
            cutter=cutter,
            file_manager=FileManager(test_config),
        )

        pipeline.run()

        assert downloader.cleanup_called
        assert cutter.cleanup_called


class TestPipelineSingleVideo:
    """Testes de processamento de vídeo único."""

    def test_process_single_video(self, test_config: Config) -> None:
        """Deve processar um vídeo e retornar stats."""
        video = test_config.temp_dir / "single.mp4"
        video.touch()

        clips = [
            Clip(
                start_time=5,
                end_time=20,
                duration=15,
                score=0.85,
                source_video=video,
            )
        ]
        results: ProcessingResults = {
            "youtube_shorts": ["/out/c1.mp4"],
            "tiktok": [],
        }

        pipeline = PipelineOrchestrator(
            config=test_config,
            downloader=FakeDownloader(),
            analyzer=FakeAnalyzer(clips),
            cutter=FakeCutter(results),
            file_manager=FileManager(test_config),
        )

        stats = pipeline.process_single_video(video)

        assert stats.analyzed_videos == 1
        assert stats.generated_clips == 1

    def test_process_no_clips_found(self, test_config: Config) -> None:
        """Quando nenhum clip é encontrado, stats deve refletir."""
        video = test_config.temp_dir / "boring.mp4"
        video.touch()

        pipeline = PipelineOrchestrator(
            config=test_config,
            downloader=FakeDownloader(),
            analyzer=FakeAnalyzer([]),
            cutter=FakeCutter(),
            file_manager=FileManager(test_config),
        )

        stats = pipeline.process_single_video(video)

        assert stats.analyzed_videos == 0
        assert stats.generated_clips == 0
