import os
import base64
import hashlib
from typing import Any
import requests  # type: ignore[import-untyped]
import structlog
import genanki  # type: ignore[import-untyped]
from anki_generator.config import settings
from anki_generator.models import Flashcard

logger = structlog.get_logger()

# Constantes do Anki
MODEL_ID = 1432958472


def stable_deck_id(deck_name: str) -> int:
    """Gera um ID de baralho determinístico a partir do nome do baralho.

    O ``hash()`` embutido do Python é randomizado por processo (via
    ``PYTHONHASHSEED``), portanto o mesmo nome de baralho produziria um ID
    diferente a cada execução. Isso faz com que o Anki trate cada importação
    como um baralho novo, criando duplicatas em vez de atualizar o existente.

    Usamos um digest SHA-256 estável para garantir que o mesmo nome sempre
    gere o mesmo ID, permitindo reimportações idempotentes.
    """
    digest = hashlib.sha256(deck_name.encode("utf-8")).hexdigest()
    return int(digest, 16) % 10**10


anki_model = genanki.Model(
    MODEL_ID,
    "anki_generator_model",
    fields=[
        {"name": "Question"},
        {"name": "AnswerText"},
        {"name": "Audio"},
        {"name": "Source"},
    ],
    templates=[
        {
            "name": "Cartão 1",
            "qfmt": "{{Question}}<br><br>{{type:AnswerText}}",
            "afmt": '{{FrontSide}}<hr id="answer">{{type:AnswerText}}<br><br>{{Audio}}<br><br><small>Fonte: {{Source}}</small>',
        },
    ],
)


def export_offline(
    deck_name: str,
    cards: list[Flashcard],
    audio_paths: dict[int, str] | None,
    output_apkg_path: str,
) -> None:
    """Gera um pacote offline .apkg contendo os cartões e as mídias associadas."""
    logger.info(
        "Iniciando exportação offline via genanki",
        deck_name=deck_name,
        output_path=output_apkg_path,
    )

    deck_id = stable_deck_id(deck_name)
    deck = genanki.Deck(deck_id, deck_name)
    media_files: list[str] = []

    for idx, card in enumerate(cards):
        audio_field = ""
        if audio_paths and idx in audio_paths:
            audio_path = audio_paths[idx]
            if os.path.exists(audio_path):
                filename = os.path.basename(audio_path)
                audio_field = f"[sound:{filename}]"
                media_files.append(audio_path)

        note = genanki.Note(
            model=anki_model,
            fields=[
                card.question,
                card.answer_text,
                audio_field,
                card.source_reference,
            ],
        )
        deck.add_note(note)

    package = genanki.Package(deck)
    package.media_files = media_files

    parent_dir = os.path.dirname(output_apkg_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    package.write_to_file(output_apkg_path)
    logger.info(
        "Exportação offline concluída com sucesso", output_path=output_apkg_path
    )


def invoke_anki_connect(action: str, **params: Any) -> Any:
    """Realiza uma chamada HTTP local para a API do AnkiConnect."""
    payload = {"action": action, "version": 6, "params": params}
    try:
        response = requests.post(settings.anki_connect_url, json=payload, timeout=5)
        response.raise_for_status()
        result = response.json()
    except Exception as e:
        logger.error(
            "Falha ao comunicar com o AnkiConnect",
            error=str(e),
            url=settings.anki_connect_url,
        )
        raise ConnectionError(f"Não foi possível conectar ao Anki: {e}") from e

    if "error" in result and result["error"] is not None:
        logger.error("Erro retornado pelo AnkiConnect", error=result["error"])
        raise ValueError(f"Erro no AnkiConnect: {result['error']}")

    return result.get("result")


def export_online(
    deck_name: str,
    cards: list[Flashcard],
    audio_paths: dict[int, str] | None,
) -> None:
    """Exporta os cartões diretamente para o Anki Desktop ativo via AnkiConnect."""
    logger.info("Iniciando exportação online via AnkiConnect", deck_name=deck_name)

    invoke_anki_connect("createDeck", deck=deck_name)

    try:
        model_names = invoke_anki_connect("modelNames")
        if "anki_generator_model" not in model_names:
            logger.info("Criando modelo de nota anki_generator_model no Anki Connect")
            invoke_anki_connect(
                "createModel",
                modelName="anki_generator_model",
                inOrderFields=["Question", "AnswerText", "Audio", "Source"],
                cardTemplates=[
                    {
                        "Name": "Cartão 1",
                        "Front": "{{Question}}<br><br>{{type:AnswerText}}",
                        "Back": '{{FrontSide}}<hr id="answer">{{type:AnswerText}}<br><br>{{Audio}}<br><br><small>Fonte: {{Source}}</small>',
                    }
                ],
            )
    except Exception as e:
        logger.warning(
            "Falha ao verificar/criar modelo personalizado, usando fallback 'Basic'",
            error=str(e),
        )

    for idx, card in enumerate(cards):
        audio_field = ""
        if audio_paths and idx in audio_paths:
            audio_path = audio_paths[idx]
            if os.path.exists(audio_path):
                filename = os.path.basename(audio_path)
                with open(audio_path, "rb") as f:
                    base64_data = base64.b64encode(f.read()).decode("utf-8")
                try:
                    invoke_anki_connect(
                        "storeMediaFile", filename=filename, data=base64_data
                    )
                    audio_field = f"[sound:{filename}]"
                except Exception as e:
                    logger.error(
                        "Falha ao enviar arquivo de mídia para o Anki",
                        filename=filename,
                        error=str(e),
                    )

        model_to_use = "anki_generator_model"
        fields = {
            "Question": card.question,
            "AnswerText": card.answer_text,
            "Audio": audio_field,
            "Source": card.source_reference,
        }

        note_payload = {
            "deckName": deck_name,
            "modelName": model_to_use,
            "fields": fields,
            "options": {
                "allowDuplicate": False,
                "duplicateScope": "deck",
            },
        }

        try:
            invoke_anki_connect("addNote", note=note_payload)
        except Exception as e:
            logger.warning(
                "Falha ao adicionar nota com modelo personalizado, tentando modelo 'Basic'",
                error=str(e),
            )
            basic_fields = {
                "Front": card.question,
                "Back": f"{card.answer_text}<br><br>{audio_field}<br><br><small>Fonte: {card.source_reference}</small>",
            }
            note_payload_basic = {
                "deckName": deck_name,
                "modelName": "Basic",
                "fields": basic_fields,
                "options": {
                    "allowDuplicate": False,
                    "duplicateScope": "deck",
                },
            }
            invoke_anki_connect("addNote", note=note_payload_basic)

    logger.info("Exportação online concluída com sucesso")
