from pathlib import Path
from unittest.mock import MagicMock, patch

from anki_generator.cli import run_cli
from anki_generator.models import ThemeSuggestion, FlashcardCollection


@patch("anki_generator.cli.scan_content_directory")
@patch("anki_generator.cli.extract_docx")
@patch("anki_generator.cli.GeminiClient")
@patch("anki_generator.cli.export_offline")
@patch("anki_generator.cli.questionary")
def test_pipeline_integration_success(
    mock_questionary: MagicMock,
    mock_export_offline: MagicMock,
    mock_gemini_client_cls: MagicMock,
    mock_extract_docx: MagicMock,
    mock_scan_dir: MagicMock,
    tmp_path: Path,
) -> None:
    # 1. Configura mocks do scan de content/
    mock_scan_dir.return_value = ["/path/to/content/file1.docx"]
    mock_extract_docx.return_value = "Conteúdo simulado de teste do Word"

    # 2. Configura mocks do questionary (perguntas e seleções da CLI)
    mock_checkbox = MagicMock()
    mock_checkbox.ask.return_value = ["file1.docx"]

    mock_text_urls = MagicMock()
    mock_text_urls.ask.return_value = ""  # sem urls do youtube

    mock_text_count = MagicMock()
    mock_text_count.ask.return_value = "3"

    mock_text_deck = MagicMock()
    mock_text_deck.ask.return_value = "Estudos"

    mock_select_lang = MagicMock()
    mock_select_lang.ask.return_value = "Portuguese"

    mock_select_modal = MagicMock()
    mock_select_modal.ask.return_value = "Text + Audio (TTS)"

    mock_select_export = MagicMock()
    mock_select_export.ask.return_value = "genanki (offline .apkg)"

    mock_questionary.checkbox.return_value = mock_checkbox
    mock_questionary.text.side_effect = [
        mock_text_urls,
        mock_text_count,
        mock_text_deck,
    ]
    mock_questionary.select.side_effect = [
        mock_select_lang,
        mock_select_modal,
        mock_select_export,
    ]

    # 3. Configura mocks do GeminiClient
    mock_gemini_instance = MagicMock()

    # Temas sugeridos
    mock_suggestion = ThemeSuggestion(
        themes=["Tema Teste"],
        suggested_cards_count=3,
        rationale="Justificativa do teste",
    )
    mock_gemini_instance.suggest_themes.return_value = mock_suggestion

    # Cartões gerados
    mock_cards = FlashcardCollection(
        cards=[
            {
                "question": "P1",
                "answer_text": "R1",
                "source_reference": "file1.docx",
            },
            {
                "question": "P2",
                "answer_text": "R2",
                "source_reference": "file1.docx",
            },
            {
                "question": "P3",
                "answer_text": "R3",
                "source_reference": "file1.docx",
            },
        ]
    )
    mock_gemini_instance.generate_flashcards.return_value = mock_cards
    mock_gemini_instance.generate_audio.return_value = b"pcm_audio_mock_bytes"

    mock_gemini_client_cls.return_value = mock_gemini_instance

    # Patch do os.path.exists para o results e content, etc.
    with patch("anki_generator.cli.os.path.exists") as mock_exists:
        mock_exists.return_value = True

        # Executa a CLI interativa simulada
        run_cli()

    assert mock_scan_dir.called
    assert mock_extract_docx.called
    assert mock_gemini_instance.suggest_themes.called
    assert mock_gemini_instance.generate_flashcards.called
    assert mock_gemini_instance.generate_audio.call_count == 3
    assert mock_export_offline.called


@patch("anki_generator.cli.scan_content_directory")
@patch("anki_generator.cli.extract_docx")
@patch("anki_generator.cli.GeminiClient")
@patch("anki_generator.cli.export_offline")
@patch("anki_generator.cli.export_online")
@patch("anki_generator.cli.questionary")
def test_pipeline_integration_online_fallback_offline(
    mock_questionary: MagicMock,
    mock_export_online: MagicMock,
    mock_export_offline: MagicMock,
    mock_gemini_client_cls: MagicMock,
    mock_extract_docx: MagicMock,
    mock_scan_dir: MagicMock,
    tmp_path: Path,
) -> None:
    # 1. Configura mocks do scan de content/
    mock_scan_dir.return_value = ["/path/to/content/file1.docx"]
    mock_extract_docx.return_value = "Conteúdo simulado"

    # 2. Configura mocks do questionary (perguntas e seleções da CLI)
    mock_checkbox = MagicMock()
    mock_checkbox.ask.return_value = ["file1.docx"]

    mock_text_urls = MagicMock()
    mock_text_urls.ask.return_value = ""

    mock_text_count = MagicMock()
    mock_text_count.ask.return_value = "1"

    mock_text_deck = MagicMock()
    mock_text_deck.ask.return_value = "JCA Operations"

    mock_select_lang = MagicMock()
    mock_select_lang.ask.return_value = "English"

    mock_select_modal = MagicMock()
    mock_select_modal.ask.return_value = "Text + Audio (TTS)"

    mock_select_export = MagicMock()
    mock_select_export.ask.return_value = "AnkiConnect (online via API)"

    mock_questionary.checkbox.return_value = mock_checkbox
    mock_questionary.text.side_effect = [
        mock_text_urls,
        mock_text_count,
        mock_text_deck,
    ]
    mock_questionary.select.side_effect = [
        mock_select_lang,
        mock_select_modal,
        mock_select_export,
    ]

    # 3. Configura mocks do GeminiClient
    mock_gemini_instance = MagicMock()
    mock_suggestion = ThemeSuggestion(
        themes=["Tema Teste"],
        suggested_cards_count=1,
        rationale="Justificativa",
    )
    mock_gemini_instance.suggest_themes.return_value = mock_suggestion

    mock_cards = FlashcardCollection(
        cards=[
            {
                "question": "P1",
                "answer_text": "R1",
                "source_reference": "file1.docx",
            }
        ]
    )
    mock_gemini_instance.generate_flashcards.return_value = mock_cards
    mock_gemini_instance.generate_audio.return_value = b"pcm"
    mock_gemini_client_cls.return_value = mock_gemini_instance

    # Força a falha na exportação online
    mock_export_online.side_effect = ConnectionError("AnkiConnect recusou conexão")

    with patch("anki_generator.cli.os.path.exists") as mock_exists:
        mock_exists.return_value = True

        run_cli()

    # Verifica que tentou exportar online, falhou, e realizou o fallback offline
    assert mock_export_online.called
    assert mock_export_offline.called
