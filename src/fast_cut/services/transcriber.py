"""Serviço de transcrição e geração de legendas."""

import logging
from pathlib import Path
from typing import Any, List, Optional, Tuple

from ..core.config import Config
from ..core.types import WordSegment

logger = logging.getLogger(__name__)

# Constantes do formato ASS
_ASS_HEADER = """\
[Script Info]
Title: FastCut Subtitles
ScriptType: v4.00+
PlayResX: {play_res_x}
PlayResY: {play_res_y}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, \
OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, \
ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, \
Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,{font_size},&H00FFFFFF,&H00FFFFFF,\
&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,0,2,40,40,{margin_v},1
Style: Highlight,Arial,{font_size},&H0000FFFF,&H0000FFFF,\
&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,0,2,40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, \
Effect, Text
"""

# Quantas palavras mostrar por bloco
_WORDS_PER_BLOCK = 3


class TranscriptionError(Exception):
    """Erro específico de transcrição."""

    pass


class VideoTranscriber:
    """Serviço de transcrição com Whisper e geração de legendas ASS."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._model: Any = None  # lazy-loaded WhisperModel

    def _ensure_model(self) -> None:
        """Carrega o modelo Whisper na primeira utilização."""
        if self._model is not None:
            return

        from faster_whisper import WhisperModel

        logger.info(
            "Carregando modelo Whisper '%s'...",
            self._config.whisper_model,
        )

        self._model = WhisperModel(
            self._config.whisper_model,
            device="cpu",
            compute_type="int8",
        )

        logger.info("Modelo Whisper carregado")

    def transcribe(self, video_path: Path) -> List[WordSegment]:
        """Transcreve um vídeo e retorna palavras com timestamps."""
        self._ensure_model()

        logger.info("Transcrevendo: %s", video_path.name)

        try:
            segments, info = self._model.transcribe(
                str(video_path),
                language=self._config.subtitle_language,
                word_timestamps=True,
                vad_filter=True,
            )

            words: List[WordSegment] = []
            for segment in segments:
                if segment.words is None:
                    continue
                for w in segment.words:
                    words.append(
                        WordSegment(
                            word=w.word.strip(),
                            start=w.start,
                            end=w.end,
                        )
                    )

            logger.info(
                "Transcrição concluída: %d palavras (idioma: %s)",
                len(words),
                info.language,
            )
            return words

        except Exception as e:
            logger.error("Erro na transcrição: %s", e)
            return []

    def generate_ass(
        self,
        words: List[WordSegment],
        output_path: Path,
        resolution: Optional[Tuple[int, int]] = None,
    ) -> Path:
        """Gera arquivo .ASS com legendas estilo viral word-by-word.

        Cada bloco de WORDS_PER_BLOCK palavras é exibido de uma vez,
        com a palavra atual destacada em amarelo e as demais em branco.
        """
        res = resolution or (1080, 1920)
        w, h = res

        # Fonte proporcional à resolução vertical
        font_size = max(28, h // 40)
        margin_v = h // 5  # ~20% da parte inferior

        content = _ASS_HEADER.format(
            play_res_x=w,
            play_res_y=h,
            font_size=font_size,
            margin_v=margin_v,
        )

        # Agrupa palavras em blocos
        blocks = _group_words(words, _WORDS_PER_BLOCK)

        for block in blocks:
            content += _build_block_dialogues(block)

        output_path.write_text(content, encoding="utf-8")

        logger.info("Legenda ASS gerada: %s", output_path.name)
        return output_path


def _group_words(words: List[WordSegment], per_block: int) -> List[List[WordSegment]]:
    """Agrupa palavras em blocos de tamanho fixo."""
    blocks: List[List[WordSegment]] = []
    for i in range(0, len(words), per_block):
        blocks.append(words[i : i + per_block])
    return blocks


def _format_ass_time(seconds: float) -> str:
    """Converte segundos para formato ASS (H:MM:SS.CC)."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _build_block_dialogues(block: List[WordSegment]) -> str:
    """Gera linhas de diálogo ASS para um bloco de palavras.

    Para cada palavra no bloco, gera uma linha onde TODAS as palavras
    são exibidas, mas a palavra "ativa" aparece com a cor Highlight
    (amarelo) e as demais em Default (branco).
    """
    if not block:
        return ""

    lines = ""
    block_end = block[-1].end

    for active_idx, active_word in enumerate(block):
        start_time = _format_ass_time(active_word.start)
        end_time = _format_ass_time(active_word.end)

        # Se é a última palavra do bloco, estende até o fim do bloco
        if active_idx == len(block) - 1:
            end_time = _format_ass_time(block_end)

        # Monta o texto com override de cor para a palavra ativa
        parts: List[str] = []
        for i, word in enumerate(block):
            if i == active_idx:
                # Palavra ativa: amarelo (\\c&H0000FFFF& em ASS BGR)
                parts.append("{\\c&H0000FFFF&}" + word.word + "{\\c&HFFFFFF&}")
            else:
                parts.append(word.word)

        text = " ".join(parts)

        lines += f"Dialogue: 0,{start_time},{end_time}," f"Default,,0,0,0,,{text}\n"

    return lines
