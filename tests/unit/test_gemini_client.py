import os
import wave
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from anki_generator.gemini_client import (
    get_voice_for_language,
    save_pcm_as_wav,
    GeminiClient,
)
from anki_generator.models import ThemeSuggestion, FlashcardCollection


def test_get_voice_for_language() -> None:
    assert get_voice_for_language("Português") == "Fenrir"
    assert get_voice_for_language("pt") == "Fenrir"
    assert get_voice_for_language("Inglês") == "Kore"
    assert get_voice_for_language("english") == "Kore"
    assert get_voice_for_language("Espanhol") == "Aoede"
    assert get_voice_for_language("spanish") == "Aoede"
    assert get_voice_for_language("Alemão") == "Kore"  # Fallback


def test_save_pcm_as_wav(tmp_path: Path) -> None:
    output = os.path.join(str(tmp_path), "test_audio.wav")
    pcm_mock = b"\x00\x01\x02\x03" * 100
    save_pcm_as_wav(output, pcm_mock, channels=1, rate=24000, sample_width=2)

    assert os.path.exists(output)
    with wave.open(output, "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2
        assert wf.getframerate() == 24000
        assert len(wf.readframes(100)) > 0


@patch("anki_generator.gemini_client.genai.Client")
def test_gemini_client_init(mock_genai_client: MagicMock) -> None:
    client = GeminiClient(api_key="custom_key")
    mock_genai_client.assert_called_once_with(api_key="custom_key")
    assert client is not None


@patch("anki_generator.gemini_client.genai.Client")
def test_suggest_themes(mock_genai_client: MagicMock) -> None:
    mock_client_instance = MagicMock()
    mock_response = MagicMock()
    mock_suggestion = ThemeSuggestion(
        themes=["Tema1", "Tema2"], suggested_cards_count=5, rationale="Justificativa"
    )
    mock_response.parsed = mock_suggestion
    mock_client_instance.models.generate_content.return_value = mock_response
    mock_genai_client.return_value = mock_client_instance

    g_client = GeminiClient(api_key="test")
    res = g_client.suggest_themes("Texto de teste")

    assert res.themes == ["Tema1", "Tema2"]
    assert res.suggested_cards_count == 5
    assert res.rationale == "Justificativa"


@patch("anki_generator.gemini_client.genai.Client")
def test_generate_flashcards(mock_genai_client: MagicMock) -> None:
    mock_client_instance = MagicMock()
    mock_response = MagicMock()
    mock_collection = FlashcardCollection(
        cards=[
            {
                "question": "Pergunta 1",
                "answer_text": "Resposta 1",
                "source_reference": "Ref 1",
            }
        ]
    )
    mock_response.parsed = mock_collection
    mock_client_instance.models.generate_content.return_value = mock_response
    mock_genai_client.return_value = mock_client_instance

    g_client = GeminiClient(api_key="test")
    res = g_client.generate_flashcards("Texto de teste", 1, "Português")

    assert len(res.cards) == 1
    assert res.cards[0].question == "Pergunta 1"
    assert res.cards[0].answer_text == "Resposta 1"


@patch("anki_generator.gemini_client.genai.Client")
def test_generate_audio_success(mock_genai_client: MagicMock) -> None:
    mock_client_instance = MagicMock()
    mock_response = MagicMock()

    mock_part = MagicMock()
    mock_part.inline_data.data = b"pcm_bytes"
    mock_candidate = MagicMock()
    mock_candidate.content.parts = [mock_part]
    mock_response.candidates = [mock_candidate]

    mock_client_instance.models.generate_content.return_value = mock_response
    mock_genai_client.return_value = mock_client_instance

    g_client = GeminiClient(api_key="test")
    res = g_client.generate_audio("Texto", "Português")
    assert res == b"pcm_bytes"


@patch("anki_generator.gemini_client.genai.Client")
def test_generate_audio_failure(mock_genai_client: MagicMock) -> None:
    mock_client_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.candidates = []

    mock_client_instance.models.generate_content.return_value = mock_response
    mock_genai_client.return_value = mock_client_instance

    g_client = GeminiClient(api_key="test")
    with pytest.raises(RuntimeError, match="Nenhum dado de áudio foi retornado"):
        g_client.generate_audio("Texto", "Português")
