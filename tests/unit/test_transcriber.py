"""Testes para o serviço de transcrição e geração de legendas."""

from pathlib import Path

from fast_cut.core.config import Config
from fast_cut.core.types import WordSegment
from fast_cut.services.transcriber import (
    VideoTranscriber,
    _build_block_dialogues,
    _format_ass_time,
    _group_words,
)


class TestFormatAssTime:
    """Testes para formatação de tempo ASS."""

    def test_zero(self) -> None:
        assert _format_ass_time(0.0) == "0:00:00.00"

    def test_seconds(self) -> None:
        assert _format_ass_time(5.5) == "0:00:05.50"

    def test_minutes(self) -> None:
        assert _format_ass_time(65.25) == "0:01:05.25"

    def test_hours(self) -> None:
        assert _format_ass_time(3661.5) == "1:01:01.50"


class TestGroupWords:
    """Testes para agrupamento de palavras em blocos."""

    def test_empty(self) -> None:
        assert _group_words([], 3) == []

    def test_exact_blocks(self) -> None:
        words = [
            WordSegment("a", 0.0, 0.5),
            WordSegment("b", 0.5, 1.0),
            WordSegment("c", 1.0, 1.5),
            WordSegment("d", 1.5, 2.0),
            WordSegment("e", 2.0, 2.5),
            WordSegment("f", 2.5, 3.0),
        ]
        blocks = _group_words(words, 3)
        assert len(blocks) == 2
        assert len(blocks[0]) == 3
        assert len(blocks[1]) == 3

    def test_partial_last_block(self) -> None:
        words = [
            WordSegment("a", 0.0, 0.5),
            WordSegment("b", 0.5, 1.0),
            WordSegment("c", 1.0, 1.5),
            WordSegment("d", 1.5, 2.0),
        ]
        blocks = _group_words(words, 3)
        assert len(blocks) == 2
        assert len(blocks[0]) == 3
        assert len(blocks[1]) == 1

    def test_single_word(self) -> None:
        words = [WordSegment("hello", 0.0, 1.0)]
        blocks = _group_words(words, 3)
        assert len(blocks) == 1
        assert len(blocks[0]) == 1


class TestBuildBlockDialogues:
    """Testes para geração de diálogos ASS."""

    def test_empty_block(self) -> None:
        assert _build_block_dialogues([]) == ""

    def test_single_word_block(self) -> None:
        block = [WordSegment("hello", 1.0, 2.0)]
        result = _build_block_dialogues(block)

        assert "Dialogue:" in result
        assert "0:00:01.00" in result
        assert "0:00:02.00" in result
        assert "hello" in result

    def test_multi_word_block_has_highlight(self) -> None:
        block = [
            WordSegment("one", 0.0, 0.5),
            WordSegment("two", 0.5, 1.0),
            WordSegment("three", 1.0, 1.5),
        ]
        result = _build_block_dialogues(block)

        # Deve ter 3 linhas de diálogo (uma por palavra ativa)
        dialogue_lines = [
            line for line in result.strip().split("\n") if line.startswith("Dialogue:")
        ]
        assert len(dialogue_lines) == 3

        # Cada linha deve conter a tag de cor highlight
        for line in dialogue_lines:
            assert "\\c&H0000FFFF&" in line

    def test_all_words_present_in_each_line(self) -> None:
        block = [
            WordSegment("foo", 0.0, 0.5),
            WordSegment("bar", 0.5, 1.0),
        ]
        result = _build_block_dialogues(block)
        lines = [
            x for x in result.strip().split("\n") if x.startswith("Dialogue:")
        ]

        # Cada linha deve conter ambas as palavras
        for line in lines:
            assert "foo" in line
            assert "bar" in line


class TestGenerateAss:
    """Testes para geração completa do arquivo ASS."""

    def test_generates_valid_ass_file(self, tmp_path: Path) -> None:
        config = Config(subtitles_enabled=True)
        transcriber = VideoTranscriber(config)

        words = [
            WordSegment("olá", 0.0, 0.5),
            WordSegment("mundo", 0.5, 1.2),
            WordSegment("teste", 1.3, 1.8),
        ]

        output = tmp_path / "test.ass"
        result = transcriber.generate_ass(words, output, (1080, 1920))

        assert result.exists()
        content = result.read_text(encoding="utf-8")

        # Verifica seções obrigatórias do ASS
        assert "[Script Info]" in content
        assert "[V4+ Styles]" in content
        assert "[Events]" in content
        assert "PlayResX: 1080" in content
        assert "PlayResY: 1920" in content

    def test_generates_dialogue_lines(self, tmp_path: Path) -> None:
        config = Config(subtitles_enabled=True)
        transcriber = VideoTranscriber(config)

        words = [
            WordSegment("a", 0.0, 0.5),
            WordSegment("b", 0.5, 1.0),
            WordSegment("c", 1.0, 1.5),
        ]

        output = tmp_path / "test.ass"
        transcriber.generate_ass(words, output, (1080, 1920))

        content = output.read_text(encoding="utf-8")
        dialogue_count = content.count("Dialogue:")

        # 1 bloco de 3 palavras = 3 dialogue lines
        assert dialogue_count == 3

    def test_empty_words_generates_header_only(self, tmp_path: Path) -> None:
        config = Config(subtitles_enabled=True)
        transcriber = VideoTranscriber(config)

        output = tmp_path / "test.ass"
        transcriber.generate_ass([], output, (1080, 1920))

        content = output.read_text(encoding="utf-8")
        assert "[Script Info]" in content
        assert "Dialogue:" not in content


class TestConfigSubtitles:
    """Testes para configuração de legendas."""

    def test_subtitles_enabled_by_default(self) -> None:
        config = Config()
        assert config.subtitles_enabled is True

    def test_whisper_model_default(self) -> None:
        config = Config()
        assert config.whisper_model == "small"

    def test_subtitle_language_default(self) -> None:
        config = Config()
        assert config.subtitle_language == "pt"

    def test_subtitles_disabled(self) -> None:
        config = Config(subtitles_enabled=False)
        assert config.subtitles_enabled is False
