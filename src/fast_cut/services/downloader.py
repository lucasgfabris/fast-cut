"""Serviço de download de vídeos."""

import json
from pathlib import Path
from typing import List, Optional

import yt_dlp

from ..core.config import Config
from ..core.types import VideoMetadata


class DownloadError(Exception):
    """Erro específico de download."""

    pass


class VideoDownloader:
    """Serviço responsável pelo download de vídeos do YouTube."""

    MIN_VIDEO_DURATION = 120  # 2 minutos

    def __init__(self) -> None:
        Config.create_directories()
        self._setup_ydl_options()

    def _setup_ydl_options(self) -> None:
        """Configura opções do yt-dlp."""
        self._ydl_opts = {
            "format": "best[height<=720]/best",
            "outtmpl": str(Config.TEMP_DIR / "%(title)s.%(ext)s"),
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
                print(f"🔍 Buscando vídeos do canal: {channel_id}")
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
            print(f"❌ Erro ao buscar vídeos do canal {channel_id}: {e}")
            return []

    def download_video(self, video: VideoMetadata) -> Optional[Path]:
        """Baixa um vídeo específico."""
        try:
            with yt_dlp.YoutubeDL(self._ydl_opts) as ydl:
                print(f"⬇️  Baixando: {video.title}")

                info = ydl.extract_info(video.url, download=False)

                if info.get("duration", 0) < self.MIN_VIDEO_DURATION:
                    print(f"⏭️  Vídeo muito curto ({info.get('duration')}s)")
                    return None

                ydl.download([video.url])
                return self._find_downloaded_file(info)

        except Exception as e:
            print(f"❌ Erro ao baixar {video.title}: {e}")
            return None

    def _find_downloaded_file(self, info: dict) -> Optional[Path]:
        """Localiza o arquivo baixado."""
        title = info.get("title", "video")
        ext = info.get("ext", "mp4")

        safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_"))
        safe_title = safe_title.strip()

        for file in Config.TEMP_DIR.glob(f"*.{ext}"):
            if safe_title[:20] in file.name:
                print(f"✅ Vídeo baixado: {file.name}")
                return file

        return None

    def download_from_channels(self, max_per_channel: int = 5) -> List[Path]:
        """Baixa vídeos de todos os canais autorizados."""
        downloaded = []

        for channel_id in Config.AUTHORIZED_CHANNELS:
            print(f"\n📺 Processando canal: {channel_id}")

            videos = self.get_channel_videos(channel_id, max_per_channel)

            for video in videos[:max_per_channel]:
                path = self.download_video(video)
                if path:
                    downloaded.append(path)

        print(f"\n✅ Download concluído: {len(downloaded)} vídeos")
        return downloaded

    def get_metadata(self, video_path: Path) -> Optional[dict]:
        """Obtém metadados de um vídeo."""
        info_path = video_path.with_suffix(".info.json")

        if info_path.exists():
            try:
                return json.loads(info_path.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"⚠️  Erro ao ler metadados: {e}")

        return None

    def cleanup(self) -> None:
        """Remove arquivos temporários de download."""
        try:
            for pattern in ["*.info.json", "*.vtt", "*.srt"]:
                for file in Config.TEMP_DIR.glob(pattern):
                    file.unlink()
            print("🧹 Arquivos temporários de download removidos")
        except Exception as e:
            print(f"⚠️  Erro na limpeza: {e}")
