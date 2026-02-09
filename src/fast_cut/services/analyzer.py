"""Serviço de análise de vídeos."""

import logging
import random
from pathlib import Path
from typing import List

import cv2
import librosa
import numpy as np
from pydub import AudioSegment
from pydub.silence import detect_nonsilent

from ..core.config import Config
from ..core.types import Clip, SpeechSegment, TimelinePoint, VideoInfo
from ..utils.ffmpeg import FFmpegUtils

logger = logging.getLogger(__name__)


class AnalysisError(Exception):
    """Erro específico de análise."""

    pass


class VideoAnalyzer:
    """Serviço responsável pela análise de vídeos."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._setup_audio_tools()

    def _setup_audio_tools(self) -> None:
        """Configura ferramentas de áudio."""
        ffmpeg = FFmpegUtils()
        ffmpeg.setup_environment()

        # Configura pydub para usar FFmpeg local (cross-platform)
        ffmpeg_path = FFmpegUtils.get_local_ffmpeg_path()
        ffprobe_path = FFmpegUtils.get_local_ffprobe_path()

        if ffmpeg_path:
            AudioSegment.converter = str(ffmpeg_path)
            AudioSegment.ffmpeg = str(ffmpeg_path)
        if ffprobe_path:
            AudioSegment.ffprobe = str(ffprobe_path)

    def get_video_info(self, video_path: Path) -> VideoInfo:
        """Obtém informações básicas do vídeo."""
        cap = cv2.VideoCapture(str(video_path))

        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = frame_count / fps if fps > 0 else 0

            return VideoInfo(
                fps=fps,
                frame_count=int(frame_count),
                width=width,
                height=height,
                duration=duration,
                aspect_ratio=width / height if height > 0 else 0,
            )

        finally:
            cap.release()

    def find_best_clips(self, video_path: Path) -> List[Clip]:
        """Encontra os melhores clipes em um vídeo."""
        logger.info("Analisando: %s", video_path.name)

        try:
            audio_path = self._extract_audio(video_path)
            energy_timeline = self._analyze_audio_energy(audio_path)
            speech_segments = self._detect_speech(audio_path)
            visual_activity = self._analyze_visual_activity(video_path)

            best_moments = self._combine_analyses(
                energy_timeline, speech_segments, visual_activity
            )

            clips = self._generate_clips(best_moments, video_path)

            # Cleanup
            audio_path.unlink(missing_ok=True)

            return clips

        except Exception as e:
            raise AnalysisError(
                f"Falha na análise de {video_path.name}: {e}"
            )

    def _extract_audio(self, video_path: Path) -> Path:
        """Extrai áudio do vídeo."""
        audio_path = video_path.parent / f"{video_path.stem}_temp_audio.wav"

        try:
            video_audio = AudioSegment.from_file(str(video_path))
            video_audio.export(str(audio_path), format="wav")
            return audio_path
        except Exception as e:
            raise AnalysisError(f"Falha na extração de áudio: {e}")

    def _analyze_audio_energy(
        self, audio_path: Path
    ) -> List[TimelinePoint]:
        """Analisa energia do áudio."""
        try:
            y, sr = librosa.load(str(audio_path))

            rms = librosa.feature.rms(
                y=y, frame_length=2048, hop_length=512
            )[0]
            times = librosa.frames_to_time(
                np.arange(len(rms)), sr=sr, hop_length=512
            )

            # Normaliza
            rms_norm = (rms - np.min(rms)) / (np.max(rms) - np.min(rms))

            return list(zip(times, rms_norm))

        except Exception as e:
            logger.warning("Erro na análise de energia: %s", e)
            return []

    def _detect_speech(self, audio_path: Path) -> List[SpeechSegment]:
        """Detecta segmentos com fala."""
        try:
            audio = AudioSegment.from_wav(str(audio_path))

            nonsilent_ranges = detect_nonsilent(
                audio,
                min_silence_len=500,
                silence_thresh=self._config.silence_threshold,
            )

            return [
                (start / 1000, end / 1000)
                for start, end in nonsilent_ranges
            ]

        except Exception as e:
            logger.warning("Erro na detecção de fala: %s", e)
            return []

    def _analyze_visual_activity(
        self, video_path: Path, sample_rate: int = 5
    ) -> List[TimelinePoint]:
        """Analisa atividade visual."""
        try:
            cap = cv2.VideoCapture(str(video_path))
            fps = cap.get(cv2.CAP_PROP_FPS)

            if fps == 0:
                return []

            frame_count = 0
            prev_frame = None
            activity_timeline: List[TimelinePoint] = []

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_count % sample_rate == 0:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    gray = cv2.GaussianBlur(gray, (21, 21), 0)

                    if prev_frame is not None:
                        frame_diff = cv2.absdiff(prev_frame, gray)
                        thresh = cv2.threshold(
                            frame_diff, 25, 255, cv2.THRESH_BINARY
                        )[1]

                        activity = np.sum(thresh) / (
                            thresh.shape[0] * thresh.shape[1]
                        )
                        timestamp = frame_count / fps

                        activity_timeline.append((timestamp, activity))

                    prev_frame = gray.copy()

                frame_count += 1

            cap.release()

            # Normaliza
            if activity_timeline:
                activities = [act for _, act in activity_timeline]
                min_act, max_act = min(activities), max(activities)

                if max_act > min_act:
                    return [
                        (ts, (act - min_act) / (max_act - min_act))
                        for ts, act in activity_timeline
                    ]

            return activity_timeline

        except Exception as e:
            logger.warning("Erro na análise visual: %s", e)
            return []

    def _combine_analyses(
        self,
        energy_timeline: List[TimelinePoint],
        speech_segments: List[SpeechSegment],
        visual_activity: List[TimelinePoint],
    ) -> List[TimelinePoint]:
        """Combina análises para encontrar melhores momentos."""
        scores: dict[float, float] = {}

        # Pontuação por energia
        for timestamp, energy in energy_timeline:
            if energy > self._config.energy_threshold:
                scores[timestamp] = scores.get(timestamp, 0) + energy * 0.4

        # Pontuação por atividade visual
        for timestamp, activity in visual_activity:
            if activity > 0.3:
                scores[timestamp] = (
                    scores.get(timestamp, 0) + activity * 0.3
                )

        # Bonificação para fala
        for start, end in speech_segments:
            for timestamp in scores:
                if start <= timestamp <= end:
                    scores[timestamp] += 0.3

        best_moments = [(ts, score) for ts, score in scores.items()]
        return sorted(best_moments, key=lambda x: x[1], reverse=True)

    def _generate_clips(
        self, best_moments: List[TimelinePoint], video_path: Path
    ) -> List[Clip]:
        """Gera clipes baseados nos melhores momentos."""
        video_info = self.get_video_info(video_path)
        clips: List[Clip] = []
        used_intervals: list[tuple[float, float]] = []

        for timestamp, score in best_moments[
            : self._config.clips_per_video * 3
        ]:
            clip_duration = random.randint(
                self._config.min_clip_duration,
                self._config.max_clip_duration,
            )

            clip_start = max(0, timestamp - clip_duration // 2)
            clip_end = min(
                video_info.duration, clip_start + clip_duration
            )

            if clip_end - clip_start < self._config.min_clip_duration:
                clip_start = max(
                    0, clip_end - self._config.min_clip_duration
                )

            # Verifica sobreposição
            overlaps = any(
                not (clip_end <= used_start or clip_start >= used_end)
                for used_start, used_end in used_intervals
            )

            if (
                not overlaps
                and len(clips) < self._config.clips_per_video
            ):
                clip = Clip(
                    start_time=clip_start,
                    end_time=clip_end,
                    duration=clip_end - clip_start,
                    score=score,
                    source_video=video_path,
                )

                if clip.is_valid:
                    clips.append(clip)
                    used_intervals.append((clip_start, clip_end))

        clips.sort(key=lambda x: x.score, reverse=True)

        logger.info("%d clipes encontrados", len(clips))
        return clips
