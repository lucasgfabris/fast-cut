"""Serviço de download de vídeos."""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional

import yt_dlp

from ..core.config import Config
from ..core.types import VideoMetadata

logger = logging.getLogger(__name__)


class DownloadError(Exception):
    """Erro específico de download."""

    pass


class VideoDownloader:
    """Serviço responsável pelo download de vídeos do YouTube."""

    MIN_VIDEO_DURATION = 120  # 2 minutos

    def __init__(self, config: Config) -> None:
        self._config = config
        self._config.create_directories()
        self._setup_ydl_options()

    def _setup_ydl_options(self) -> None:
        """Configura opções do yt-dlp."""
        self._ydl_opts = {
            "format": "best[height<=1080]/best",
            "outtmpl": str(self._config.temp_dir / "fastcut_original_%(id)s.%(ext)s"),
            "writeinfojson": True,
            "writesubtitles": False,
            "writeautomaticsub": False,
            "ignoreerrors": True,
            "no_warnings": False,
            "extract_flat": False,
            "noplaylist": True,
        }

    def get_channel_videos(
        self, channel_id: str, max_videos: int = 10
    ) -> List[VideoMetadata]:
        """Obtém vídeos de um canal."""
        channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"

        list_opts = {
            "quiet": True,
            "extract_flat": True,
            "playlistend": max_videos,
        }

        try:
            with yt_dlp.YoutubeDL(list_opts) as ydl:
                logger.info("Buscando vídeos do canal: %s", channel_id)
                playlist_info = ydl.extract_info(channel_url, download=False)

                if not playlist_info or "entries" not in playlist_info:
                    return []

                return [
                    VideoMetadata(
                        id=entry["id"],
                        title=entry.get("title", "Título não disponível"),
                        url=entry["url"],
                        duration=entry.get("duration"),
                        upload_date=entry.get("upload_date"),
                        view_count=entry.get("view_count"),
                        channel_id=channel_id,
                    )
                    for entry in playlist_info["entries"]
                    if entry
                ]

        except Exception as e:
            logger.error("Erro ao buscar vídeos do canal %s: %s", channel_id, e)
            return []

    def download_video(self, video: VideoMetadata) -> Optional[Path]:
        """Baixa um vídeo específico."""
        try:
            with yt_dlp.YoutubeDL(self._ydl_opts) as ydl:
                logger.info("Baixando: %s", video.title)

                info = ydl.extract_info(video.url, download=False)

                if info.get("duration", 0) < self.MIN_VIDEO_DURATION:
                    logger.info("Vídeo muito curto (%ds)", info.get("duration"))
                    return None

                ydl.download([video.url])
                return self._find_downloaded_file(info)

        except Exception as e:
            logger.error("Erro ao baixar %s: %s", video.title, e)
            return None

    def _find_downloaded_file(self, info: dict) -> Optional[Path]:
        """Localiza o arquivo baixado."""
        video_id = info.get("id", "")
        ext = info.get("ext", "mp4")

        if not video_id:
            return None

        expected_file = self._config.temp_dir / f"fastcut_original_{video_id}.{ext}"

        if expected_file.exists():
            logger.info("Vídeo baixado: %s", expected_file.name)
            return expected_file

        return None

    def download_from_channels(self, max_per_channel: int = 5) -> List[Path]:
        """Baixa vídeos de todos os canais autorizados (paralelo por canal)."""
        # Coleta todos os vídeos de todos os canais
        all_videos: List[VideoMetadata] = []
        for channel_id in self._config.authorized_channels:
            logger.info("Processando canal: %s", channel_id)
            videos = self.get_channel_videos(channel_id, max_per_channel)
            all_videos.extend(videos[:max_per_channel])

        if not all_videos:
            logger.info("Nenhum vídeo encontrado nos canais")
            return []

        # Downloads em paralelo (max 3 simultâneos para não sobrecarregar)
        downloaded: List[Path] = []
        max_workers = min(3, len(all_videos))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.download_video, video): video
                for video in all_videos
            }

            for future in as_completed(futures):
                video = futures[future]
                try:
                    path = future.result()
                    if path:
                        downloaded.append(path)
                except Exception as e:
                    logger.error("Erro no download de %s: %s", video.title, e)

        logger.info("Download concluído: %d vídeos", len(downloaded))
        return downloaded

    def get_metadata(self, video_path: Path) -> Optional[Dict[str, Any]]:
        """Obtém metadados de um vídeo."""
        info_path = video_path.with_suffix(".info.json")

        if info_path.exists():
            try:
                data: Dict[str, Any] = json.loads(info_path.read_text(encoding="utf-8"))
                return data
            except Exception as e:
                logger.warning("Erro ao ler metadados: %s", e)

        return None

    def cleanup(self) -> None:
        """Remove arquivos temporários de download."""
        try:
            for pattern in ["*.info.json", "*.vtt", "*.srt"]:
                for file in self._config.temp_dir.glob(pattern):
                    file.unlink()
            logger.info("Arquivos temporários de download removidos")
        except Exception as e:
            logger.warning("Erro na limpeza: %s", e)
