from pathlib import Path
from unittest.mock import MagicMock, patch

from anki_generator.cli import (
    build_parser,
    main,
    resolve_input_files,
    run_noninteractive,
)
from anki_generator.models import ThemeSuggestion


def test_build_parser_defaults() -> None:
    args = build_parser().parse_args([])
    assert args.language == "portuguese"
    assert args.modality == "text"
    assert args.export == "offline"
    assert args.count is None
    assert args.file is None
    assert args.youtube is None
    assert args.non_interactive is False


def test_build_parser_repeatable_sources() -> None:
    args = build_parser().parse_args(
        ["-f", "a.pdf", "--file", "b.docx", "-y", "http://yt/1"]
    )
    assert args.file == ["a.pdf", "b.docx"]
    assert args.youtube == ["http://yt/1"]


def test_resolve_input_files_path_and_content_dir(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    direct = tmp_path / "direct.pdf"
    direct.write_text("x")
    (content / "inside.docx").write_text("y")

    resolved = resolve_input_files(
        [str(direct), "inside.docx", "missing.pdf", "bad.txt"], str(content)
    )
    assert str(direct) in resolved
    assert str(content / "inside.docx") in resolved
    # missing file and unsupported extension are skipped
    assert len(resolved) == 2


@patch("anki_generator.cli.generate_and_export")
@patch("anki_generator.cli.extract_combined_text")
@patch("anki_generator.cli.GeminiClient")
def test_run_noninteractive_with_explicit_count(
    mock_client_cls: MagicMock,
    mock_extract: MagicMock,
    mock_gen_export: MagicMock,
) -> None:
    mock_extract.return_value = "some study text"
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    args = build_parser().parse_args(
        ["-y", "http://yt/abc", "-n", "5", "-l", "en", "-m", "audio", "-d", "Deck X"]
    )
    rc = run_noninteractive(args)

    assert rc == 0
    # suggest_themes must NOT be called when --count is explicit
    mock_client.suggest_themes.assert_not_called()
    call = mock_gen_export.call_args
    # count, language, modality, export are positional after client + text
    assert call.args[2] == 5
    assert call.args[3] == "English"
    assert call.args[4] == "Text + Audio (TTS)"
    assert call.args[5] == "genanki (offline .apkg)"
    assert call.args[6] == "Deck X"


@patch("anki_generator.cli.generate_and_export")
@patch("anki_generator.cli.extract_combined_text")
@patch("anki_generator.cli.GeminiClient")
def test_run_noninteractive_suggests_count_when_omitted(
    mock_client_cls: MagicMock,
    mock_extract: MagicMock,
    mock_gen_export: MagicMock,
) -> None:
    mock_extract.return_value = "text"
    mock_client = MagicMock()
    mock_client.suggest_themes.return_value = ThemeSuggestion(
        themes=["t"], suggested_cards_count=7, rationale="r"
    )
    mock_client_cls.return_value = mock_client

    args = build_parser().parse_args(["-f", "x.docx", "-y", "http://yt/abc"])
    # patch resolve so the missing file does not get filtered out
    with patch("anki_generator.cli.resolve_input_files", return_value=["x.docx"]):
        rc = run_noninteractive(args)

    assert rc == 0
    mock_client.suggest_themes.assert_called_once()
    assert mock_gen_export.call_args.args[2] == 7


@patch("anki_generator.cli.GeminiClient")
def test_run_noninteractive_requires_a_source(mock_client_cls: MagicMock) -> None:
    args = build_parser().parse_args(["--non-interactive"])
    rc = run_noninteractive(args)
    assert rc == 1
    mock_client_cls.assert_not_called()


@patch("anki_generator.cli.extract_combined_text", return_value="   ")
@patch("anki_generator.cli.GeminiClient")
def test_run_noninteractive_empty_extraction(
    mock_client_cls: MagicMock, mock_extract: MagicMock
) -> None:
    args = build_parser().parse_args(["-y", "http://yt/abc"])
    rc = run_noninteractive(args)
    assert rc == 1


@patch("anki_generator.cli.run_cli")
def test_main_dispatches_to_interactive_without_flags(mock_run_cli: MagicMock) -> None:
    rc = main([])
    assert rc == 0
    mock_run_cli.assert_called_once()


@patch("anki_generator.cli.run_noninteractive", return_value=0)
def test_main_dispatches_to_noninteractive_with_file(
    mock_run_ni: MagicMock,
) -> None:
    rc = main(["-f", "a.pdf"])
    assert rc == 0
    mock_run_ni.assert_called_once()
