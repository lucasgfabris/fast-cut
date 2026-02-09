"""Protocols (interfaces) para os serviços do sistema."""

from pathlib import Path
from typing import List, Optional, Protocol

from .types import Clip, ProcessingResults, VideoMetadata, WordSegment


class Downloader(Protocol):
    """Interface para serviço de download de vídeos."""

    def download_from_channels(self, max_per_channel: int = 5) -> List[Path]:
        """Baixa vídeos de todos os canais autorizados."""
        ...

    def download_video(self, video: VideoMetadata) -> Optional[Path]:
        """Baixa um vídeo específico."""
        ...

    def get_channel_videos(
        self, channel_id: str, max_videos: int = 10
    ) -> List[VideoMetadata]:
        """Obtém vídeos de um canal."""
        ...

    def cleanup(self) -> None:
        """Remove arquivos temporários."""
        ...


class Analyzer(Protocol):
    """Interface para serviço de análise de vídeos."""

    def find_best_clips(self, video_path: Path) -> List[Clip]:
        """Encontra os melhores clipes em um vídeo."""
        ...


class Transcriber(Protocol):
    """Interface para serviço de transcrição de vídeos."""

    def transcribe(self, video_path: Path) -> List[WordSegment]:
        """Transcreve um vídeo e retorna palavras com timestamps."""
        ...

    def generate_ass(
        self,
        words: List[WordSegment],
        output_path: Path,
        resolution: tuple,
    ) -> Path:
        """Gera arquivo .ASS com legendas estilo viral."""
        ...


class Cutter(Protocol):
    """Interface para serviço de corte de vídeos."""

    def process_clips(
        self,
        clips: List[Clip],
        source_video: Path,
        video_num: int = 1,
        total_videos: int = 1,
    ) -> ProcessingResults:
        """Processa uma lista de clipes para todas as plataformas."""
        ...

    def cleanup(self) -> None:
        """Remove arquivos temporários."""
        ...
