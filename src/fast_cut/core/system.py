"""Sistema principal do Fast Cut."""

import sys
from datetime import datetime
from pathlib import Path
from typing import List

from .config import Config
from .types import ProcessingStats
from ..services.analyzer import VideoAnalyzer
from ..services.cutter import VideoCutter
from ..services.downloader import VideoDownloader


class FastCutSystem:
    """Sistema principal para geração automática de cortes."""

    def __init__(self, show_header: bool = True) -> None:
        try:
            Config.validate()
            Config.create_directories()

            self._downloader = VideoDownloader()
            self._analyzer = VideoAnalyzer()
            self._cutter = VideoCutter()

            if show_header:
                self._print_header()

        except Exception as e:
            print(f"❌ Erro na inicialização: {e}")
            sys.exit(1)

    def run_full_pipeline(
        self, max_videos_per_channel: int = 5, skip_download: bool = False
    ) -> ProcessingStats:
        """Executa o pipeline completo."""
        stats = ProcessingStats()
        stats.clips_by_platform = {platform: 0 for platform in Config.PLATFORM_SPECS}

        try:
            start_time = datetime.now()

            # Etapa 1: Download
            videos = self._download_phase(max_videos_per_channel, skip_download)
            stats.downloaded_videos = len(videos)

            if not videos:
                print("❌ Nenhum vídeo disponível para processamento")
                return stats

            # Etapa 2: Análise e Corte
            self._processing_phase(videos, stats)

            # Etapa 3: Limpeza
            self._cleanup_phase()

            # Relatório
            duration = datetime.now() - start_time
            self._print_final_report(stats, duration)

            return stats

        except Exception as e:
            error_msg = f"Erro crítico no pipeline: {e}"
            print(f"❌ {error_msg}")
            stats.errors.append(error_msg)
            return stats

    def _download_phase(
        self, max_videos_per_channel: int, skip_download: bool
    ) -> List[Path]:
        """Fase de download de vídeos."""
        print("🔽 ETAPA 1: DOWNLOAD DE VÍDEOS")
        print("-" * 40)

        if skip_download:
            videos = self._get_existing_videos()
            print(f"📁 Usando {len(videos)} vídeos existentes")
        else:
            videos = self._downloader.download_from_channels(max_videos_per_channel)
            print(f"✅ {len(videos)} vídeos baixados")

        return videos

    def _get_existing_videos(self) -> List[Path]:
        """Obtém vídeos existentes no diretório temp."""
        extensions = [".mp4", ".mkv", ".avi", ".mov"]
        return [
            file
            for file in Config.TEMP_DIR.iterdir()
            if file.suffix.lower() in extensions
        ]

    def _processing_phase(self, videos: List[Path], stats: ProcessingStats) -> None:
        """Fase de processamento dos vídeos."""
        print("\n🔍 ETAPA 2: ANÁLISE E GERAÇÃO DE CORTES")
        print("-" * 40)

        for i, video_path in enumerate(videos, 1):
            print(f"\n📹 Processando {i}/{len(videos)}: {video_path.name}")

            try:
                # Analisa vídeo
                clips = self._analyzer.find_best_clips(video_path)

                if not clips:
                    print("⚠️  Nenhum clipe interessante encontrado")
                    stats.errors.append(f"Sem clipes em {video_path.name}")
                    continue

                stats.analyzed_videos += 1

                # Gera cortes
                results = self._cutter.process_clips(clips, video_path)

                # Contabiliza resultados
                video_clips_count = 0
                for platform, platform_clips in results.items():
                    count = len(platform_clips)
                    stats.clips_by_platform[platform] += count
                    video_clips_count += count

                stats.generated_clips += video_clips_count
                print(f"✅ {video_clips_count} clipes gerados")

            except Exception as e:
                error_msg = f"Erro em {video_path.name}: {e}"
                print(f"❌ {error_msg}")
                stats.errors.append(error_msg)

    def _cleanup_phase(self) -> None:
        """Fase de limpeza."""
        print("\n🧹 ETAPA 3: LIMPEZA")
        print("-" * 40)

        self._downloader.cleanup()
        self._cutter.cleanup()

    def _print_header(self) -> None:
        """Imprime cabeçalho do sistema."""
        print("=" * 60)
        print("🎬 SISTEMA FAST CUT - GERADOR AUTOMÁTICO DE CORTES")
        print("=" * 60)
        print(f"Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print()

    def _print_final_report(self, stats: ProcessingStats, duration) -> None:
        """Imprime relatório final."""
        print("=" * 60)
        print("📊 RELATÓRIO FINAL")
        print("=" * 60)

        print(f"⏱️  Tempo de execução: {duration}")
        print(f"📥 Vídeos baixados: {stats.downloaded_videos}")
        print(f"🔍 Vídeos analisados: {stats.analyzed_videos}")
        print(f"✂️  Total de clipes: {stats.generated_clips}")
        print()

        print("📱 CLIPES POR PLATAFORMA:")
        for platform, count in stats.clips_by_platform.items():
            platform_name = platform.replace("_", " ").title()
            print(f"  {platform_name}: {count} clipes")

        if stats.errors:
            print(f"\n⚠️  ERROS ({len(stats.errors)}):")
            for error in stats.errors[:5]:  # Mostra apenas os primeiros 5
                print(f"  - {error}")
            if len(stats.errors) > 5:
                print(f"  ... e mais {len(stats.errors) - 5} erros")

        if stats.analyzed_videos > 0:
            success_rate = (stats.analyzed_videos / stats.downloaded_videos) * 100
            print(f"\n📈 Taxa de sucesso: {success_rate:.1f}%")

        print(f"🎯 Clipes salvos em: {Config.OUTPUT_DIR}")
        print("=" * 60)

    def list_channels(self) -> None:
        """Lista canais autorizados."""
        print("\n📺 CANAIS AUTORIZADOS:")
        print("-" * 30)

        if not Config.AUTHORIZED_CHANNELS:
            print("❌ Nenhum canal configurado")
            print("Configure AUTHORIZED_CHANNELS no arquivo .env")
            return

        for i, channel_id in enumerate(Config.AUTHORIZED_CHANNELS, 1):
            print(f"{i}. {channel_id}")

            try:
                videos = self._downloader.get_channel_videos(channel_id, 1)
                if videos:
                    print(f"   ✅ Ativo - último: {videos[0].title[:50]}...")
                else:
                    print("   ⚠️  Sem vídeos recentes")
            except Exception:
                print("   ❌ Erro de acesso")

        print(f"\nTotal: {len(Config.AUTHORIZED_CHANNELS)} canais")

    def test_system(self) -> None:
        """Testa o sistema com vídeo existente."""
        print("🧪 TESTE DO SISTEMA")
        print("-" * 30)

        videos = self._get_existing_videos()

        if not videos:
            print("❌ Nenhum vídeo para teste")
            print(f"Coloque um vídeo em: {Config.TEMP_DIR}")
            return

        test_video = videos[0]
        print(f"📹 Testando com: {test_video.name}")

        try:
            clips = self._analyzer.find_best_clips(test_video)

            if clips:
                print(f"✅ {len(clips)} clipes encontrados")

                results = self._cutter.process_clips(clips[:1], test_video)
                total = sum(len(platform_clips) for platform_clips in results.values())

                print(f"✅ {total} clipes de teste gerados")

                for platform, platform_clips in results.items():
                    if platform_clips:
                        print(f"  {platform}: {Path(platform_clips[0]).name}")
            else:
                print("❌ Nenhum clipe encontrado")

        except Exception as e:
            print(f"❌ Erro no teste: {e}")
