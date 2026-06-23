from anki_generator.models import ThemeSuggestion, FlashcardCollection


def test_theme_suggestion_validation() -> None:
    data = {
        "themes": ["História", "Geografia"],
        "suggested_cards_count": 10,
        "rationale": "Baseado na quantidade de tópicos.",
    }
    obj = ThemeSuggestion(**data)
    assert obj.themes == ["História", "Geografia"]
    assert obj.suggested_cards_count == 10
    assert obj.rationale == "Baseado na quantidade de tópicos."


def test_flashcard_collection_validation() -> None:
    data = {
        "cards": [
            {
                "question": "Qual a capital da França?",
                "answer_text": "Paris",
                "source_reference": "Documento de Geografia",
            }
        ]
    }
    collection = FlashcardCollection(**data)
    assert len(collection.cards) == 1
    assert collection.cards[0].question == "Qual a capital da França?"
    assert collection.cards[0].answer_text == "Paris"
