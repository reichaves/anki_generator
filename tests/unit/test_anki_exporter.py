import os
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Any
import pytest

from anki_generator.models import Flashcard
from anki_generator.anki_exporter import (
    export_offline,
    export_online,
    invoke_anki_connect,
    stable_deck_id,
)


def test_stable_deck_id_is_deterministic() -> None:
    """O mesmo nome deve sempre gerar o mesmo ID (independente de PYTHONHASHSEED)."""
    assert stable_deck_id("Brazilian History") == stable_deck_id("Brazilian History")


def test_stable_deck_id_differs_per_name() -> None:
    """Nomes diferentes devem gerar IDs diferentes."""
    assert stable_deck_id("Deck A") != stable_deck_id("Deck B")


def test_stable_deck_id_in_valid_range() -> None:
    """O ID deve ser um inteiro positivo dentro do intervalo esperado pelo genanki."""
    deck_id = stable_deck_id("Estudos")
    assert isinstance(deck_id, int)
    assert 0 < deck_id < 10**10


def test_stable_deck_id_known_value() -> None:
    """Trava um valor conhecido para detectar mudanças acidentais no algoritmo."""
    # SHA-256("Estudos") -> int -> % 10**10
    assert stable_deck_id("Estudos") == 4346935940


def test_export_offline(tmp_path: Path) -> None:
    output_apkg = os.path.join(str(tmp_path), "results", "output.apkg")
    audio_temp = os.path.join(str(tmp_path), "audio1.wav")
    with open(audio_temp, "w") as f:
        f.write("audio_data")

    cards = [
        Flashcard(
            question="Qual o símbolo do Ouro?",
            answer_text="Au",
            source_reference="Tabela Periódica",
        )
    ]
    audio_paths = {0: audio_temp}

    with patch("genanki.Package.write_to_file") as mock_write:
        export_offline("Test Deck", cards, audio_paths, output_apkg)
        mock_write.assert_called_once_with(output_apkg)


@patch("anki_generator.anki_exporter.requests.post")
def test_invoke_anki_connect_success(mock_post: MagicMock) -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"result": "success_deck_id", "error": None}
    mock_post.return_value = mock_resp

    res = invoke_anki_connect("createDeck", deck="Novo Baralho")
    assert res == "success_deck_id"


@patch("anki_generator.anki_exporter.requests.post")
def test_invoke_anki_connect_error(mock_post: MagicMock) -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"result": None, "error": "Deck already exists"}
    mock_post.return_value = mock_resp

    with pytest.raises(ValueError, match="Erro no AnkiConnect: Deck already exists"):
        invoke_anki_connect("createDeck", deck="Novo Baralho")


@patch("anki_generator.anki_exporter.requests.post")
def test_invoke_anki_connect_http_failure(mock_post: MagicMock) -> None:
    mock_post.side_effect = Exception("HTTP 500 Connection Refused")

    with pytest.raises(ConnectionError, match="Não foi possível conectar ao Anki"):
        invoke_anki_connect("createDeck", deck="Novo Baralho")


@patch("anki_generator.anki_exporter.requests.post")
def test_export_online_success(mock_post: MagicMock, tmp_path: Path) -> None:
    def post_side_effect(*args: Any, **kwargs: Any) -> MagicMock:
        json_data = kwargs.get("json", {})
        action = json_data.get("action")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        if action == "modelNames":
            mock_resp.json.return_value = {"result": ["Basic"], "error": None}
        else:
            mock_resp.json.return_value = {"result": "success", "error": None}
        return mock_resp

    mock_post.side_effect = post_side_effect

    audio_temp = os.path.join(str(tmp_path), "audio1.wav")
    with open(audio_temp, "w") as f:
        f.write("audio_data")

    cards = [
        Flashcard(
            question="Pergunta",
            answer_text="Resposta",
            source_reference="Fonte",
        )
    ]
    audio_paths = {0: audio_temp}

    export_online("Meu Deck", cards, audio_paths)
    assert mock_post.call_count >= 3
