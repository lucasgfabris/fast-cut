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

        total_videos = len(videos)
        
        for i, video_path in enumerate(videos, 1):
            progress = (i / total_videos) * 100
            print(f"\n📹 Processando {i}/{total_videos} ({progress:.1f}%): {video_path.name}")

            try:
                # Analisa vídeo
                clips = self._analyzer.find_best_clips(video_path)

                if not clips:
                    print("⚠️  Nenhum clipe interessante encontrado")
                    stats.errors.append(f"Sem clipes em {video_path.name}")
                    continue

                stats.analyzed_videos += 1

                # Gera cortes com progresso
                results = self._cutter.process_clips(clips, video_path, i, total_videos)

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
        self._cleanup_temp_videos()

    def _cleanup_temp_videos(self) -> None:
        """Remove vídeos baixados da pasta temp após processamento."""
        try:
            removed_count = 0
            
            # Remove vídeos originais baixados (fastcut_original_*)
            for file in Config.TEMP_DIR.glob("fastcut_original_*"):
                if file.is_file():
                    file.unlink()
                    removed_count += 1
            
            if removed_count > 0:
                print(f"🗑️  {removed_count} vídeo(s) original(is) removido(s) de temp/")
        except Exception as e:
            print(f"⚠️  Erro ao limpar vídeos temporários: {e}")

    def clear_all_outputs(self) -> None:
        """Limpa todas as pastas de saída e temporários."""
        import shutil
        
        print("🧹 LIMPANDO DIRETÓRIOS")
        print("-" * 40)
        
        try:
            # Limpa output/
            if Config.OUTPUT_DIR.exists():
                removed_count = 0
                for platform_dir in Config.OUTPUT_DIR.iterdir():
                    if platform_dir.is_dir():
                        for file in platform_dir.iterdir():
                            if file.is_file():
                                file.unlink()
                                removed_count += 1
                print(f"✅ {removed_count} arquivo(s) removido(s) de output/")
            
            # Limpa temp/
            if Config.TEMP_DIR.exists():
                removed_count = 0
                for file in Config.TEMP_DIR.iterdir():
                    if file.is_file():
                        file.unlink()
                        removed_count += 1
                print(f"✅ {removed_count} arquivo(s) removido(s) de temp/")
            
            print("✅ Limpeza concluída!")
        except Exception as e:
            print(f"❌ Erro durante limpeza: {e}")

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

    def process_specific_video(self, video_path_str: str) -> ProcessingStats:
        """Processa um vídeo específico (arquivo local ou URL do YouTube)."""
        stats = ProcessingStats()
        stats.clips_by_platform = {platform: 0 for platform in Config.PLATFORM_SPECS}
        
        print("🎬 PROCESSAMENTO DE VÍDEO ESPECÍFICO")
        print("=" * 60)
        
        # Verifica se é uma URL do YouTube
        if video_path_str.startswith(("http://", "https://", "www.")):
            print(f"🔗 Link detectado: {video_path_str}")
            print("⬇️  Baixando vídeo...")
            
            try:
                from .types import VideoMetadata
                
                # Cria metadata temporário para o vídeo
                video_metadata = VideoMetadata(
                    id="",
                    title="Video específico",
                    url=video_path_str,
                    duration=None,
                    upload_date=None,
                    view_count=None,
                    channel_id=""
                )
                
                # Baixa o vídeo
                video_path = self._downloader.download_video(video_metadata)
                
                if not video_path:
                    print("❌ Falha ao baixar o vídeo")
                    return stats
                
                print(f"✅ Vídeo baixado: {video_path.name}")
                
            except Exception as e:
                print(f"❌ Erro ao baixar vídeo: {e}")
                return stats
        else:
            # É um caminho de arquivo local
            video_path = Path(video_path_str)
            
            if not video_path.exists():
                print(f"❌ Vídeo não encontrado: {video_path}")
                return stats
            
            if not video_path.is_file():
                print(f"❌ Caminho não é um arquivo: {video_path}")
                return stats
        
        try:
            from datetime import datetime
            start_time = datetime.now()
            
            print(f"📹 Processando: {video_path.name}")
            print("-" * 60)
            
            # Analisa vídeo
            print("🔍 Analisando vídeo...")
            clips = self._analyzer.find_best_clips(video_path)
            
            if not clips:
                print("⚠️  Nenhum clipe interessante encontrado")
                return stats
            
            stats.analyzed_videos = 1
            print(f"✅ {len(clips)} clipes encontrados")
            
            # Gera cortes
            print("\n✂️  Gerando cortes...")
            results = self._cutter.process_clips(clips, video_path, 1, 1)
            
            # Contabiliza resultados
            video_clips_count = 0
            for platform, platform_clips in results.items():
                count = len(platform_clips)
                stats.clips_by_platform[platform] += count
                video_clips_count += count
            
            stats.generated_clips += video_clips_count
            
            # Relatório
            duration = datetime.now() - start_time
            print("\n" + "=" * 60)
            print("📊 RESULTADO")
            print("=" * 60)
            print(f"⏱️  Tempo: {duration}")
            print(f"✂️  Total de clipes: {video_clips_count}")
            print()
            print("📱 CLIPES POR PLATAFORMA:")
            for platform, count in stats.clips_by_platform.items():
                platform_name = platform.replace("_", " ").title()
                print(f"  {platform_name}: {count} clipes")
            print(f"\n🎯 Clipes salvos em: {Config.OUTPUT_DIR}")
            print("=" * 60)
            
            return stats
            
        except Exception as e:
            error_msg = f"Erro ao processar vídeo: {e}"
            print(f"❌ {error_msg}")
            stats.errors.append(error_msg)
            return stats

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
