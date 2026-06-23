import os
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from youtube_transcript_api import TranscriptsDisabled

from anki_generator.extractors import (
    validate_safe_path,
    extract_youtube_video_id,
    extract_youtube_transcript,
    TranscriptUnavailableError,
    scan_content_directory,
    extract_docx,
    extract_pdf,
    ExtractorError,
)


def test_validate_safe_path_valid() -> None:
    base = os.path.abspath("content")
    target = os.path.abspath(os.path.join("content", "file.pdf"))
    assert validate_safe_path(base, target) == target


def test_validate_safe_path_invalid() -> None:
    base = os.path.abspath("content")
    target = os.path.abspath("outside.pdf")
    with pytest.raises(ValueError, match="fora do diretório permitido"):
        validate_safe_path(base, target)


def test_extract_youtube_video_id() -> None:
    valid_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://youtube.com/shorts/dQw4w9WgXcQ",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
        "dQw4w9WgXcQ",  # Fallback
    ]
    for url in valid_urls:
        assert extract_youtube_video_id(url) == "dQw4w9WgXcQ"

    with pytest.raises(ValueError, match="Não foi possível extrair"):
        extract_youtube_video_id("https://example.com/not-youtube")


@patch("anki_generator.extractors.YouTubeTranscriptApi.get_transcript")
def test_extract_youtube_transcript_success(mock_get_transcript: MagicMock) -> None:
    mock_get_transcript.return_value = [
        {"text": "Hello world", "start": 0.0, "duration": 2.0},
        {"text": "Anki is great", "start": 2.0, "duration": 3.0},
    ]
    entries = extract_youtube_transcript("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert len(entries) == 2
    assert entries[0]["text"] == "Hello world"
    assert entries[0]["start"] == 0.0
    assert entries[1]["duration"] == 3.0


@patch("anki_generator.extractors.YouTubeTranscriptApi.get_transcript")
def test_extract_youtube_transcript_disabled(mock_get_transcript: MagicMock) -> None:
    mock_get_transcript.side_effect = TranscriptsDisabled("Video ID")
    with pytest.raises(
        TranscriptUnavailableError, match="Transcrições desativadas ou indisponíveis"
    ):
        extract_youtube_transcript("https://www.youtube.com/watch?v=dQw4w9WgXcQ")


@patch("anki_generator.extractors.YouTubeTranscriptApi.get_transcript")
def test_extract_youtube_transcript_generic_error(
    mock_get_transcript: MagicMock,
) -> None:
    mock_get_transcript.side_effect = Exception("API error")
    with pytest.raises(TranscriptUnavailableError, match="Erro ao obter transcrição"):
        extract_youtube_transcript("https://www.youtube.com/watch?v=dQw4w9WgXcQ")


@patch("anki_generator.extractors.Document")
def test_extract_docx_success(mock_document: MagicMock) -> None:
    mock_doc_instance = MagicMock()
    mock_p1 = MagicMock()
    mock_p1.text = "Hello Word"
    mock_p2 = MagicMock()
    mock_p2.text = "Second line"
    mock_doc_instance.paragraphs = [mock_p1, mock_p2]
    mock_document.return_value = mock_doc_instance

    result = extract_docx("dummy.docx")
    assert result == "Hello Word\nSecond line"


@patch("anki_generator.extractors.Document")
def test_extract_docx_error(mock_document: MagicMock) -> None:
    mock_document.side_effect = Exception("File load error")
    with pytest.raises(ExtractorError, match="Falha ao extrair texto"):
        extract_docx("dummy.docx")


@patch("anki_generator.extractors.PdfReader")
def test_extract_pdf_success(mock_pdf_reader: MagicMock) -> None:
    mock_reader_instance = MagicMock()
    mock_page1 = MagicMock()
    mock_page1.extract_text.return_value = "Hello PDF"
    mock_page2 = MagicMock()
    mock_page2.extract_text.return_value = "Second Page"
    mock_reader_instance.pages = [mock_page1, mock_page2]
    mock_pdf_reader.return_value = mock_reader_instance

    result = extract_pdf("dummy.pdf")
    assert result == "Hello PDF\nSecond Page"


@patch("anki_generator.extractors.PdfReader")
def test_extract_pdf_error(mock_pdf_reader: MagicMock) -> None:
    mock_pdf_reader.side_effect = Exception("File load error")
    with pytest.raises(ExtractorError, match="Falha ao extrair texto"):
        extract_pdf("dummy.pdf")


def test_scan_content_directory(tmp_path: Path) -> None:
    content_dir = str(tmp_path)
    with open(os.path.join(content_dir, "file1.docx"), "w") as f:
        f.write("docx")
    with open(os.path.join(content_dir, "file2.pdf"), "w") as f:
        f.write("pdf")
    with open(os.path.join(content_dir, ".gitkeep"), "w") as f:
        f.write("gitkeep")
    with open(os.path.join(content_dir, "other.txt"), "w") as f:
        f.write("text")

    files = scan_content_directory(content_dir)
    assert len(files) == 2
    assert any(f.endswith("file1.docx") for f in files)
    assert any(f.endswith("file2.pdf") for f in files)
