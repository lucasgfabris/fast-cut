"""Tipos e estruturas de dados do sistema."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class VideoInfo:
    """Informações básicas de um vídeo."""

    fps: float
    frame_count: int
    width: int
    height: int
    duration: float
    aspect_ratio: float


@dataclass
class VideoMetadata:
    """Metadados de um vídeo baixado."""

    id: str
    title: str
    url: str
    duration: Optional[int]
    upload_date: Optional[str]
    view_count: Optional[int]
    channel_id: str


@dataclass
class Clip:
    """Representa um clipe de vídeo."""

    start_time: float
    end_time: float
    duration: float
    score: float
    source_video: Path

    @property
    def is_valid(self) -> bool:
        """Verifica se o clipe é válido."""
        return self.duration > 0 and self.start_time < self.end_time


@dataclass
class ProcessingStats:
    """Estatísticas de processamento."""

    downloaded_videos: int = 0
    analyzed_videos: int = 0
    generated_clips: int = 0
    clips_by_platform: Dict[str, int] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


TimelinePoint = Tuple[float, float]  # (timestamp, value)
SpeechSegment = Tuple[float, float]  # (start_time, end_time)
ProcessingResults = Dict[str, List[str]]  # platform -> list of file paths
