from pydantic import BaseModel, Field


class ThemeSuggestion(BaseModel):
    themes: list[str] = Field(
        description="Lista de temas ou tópicos identificados no texto."
    )
    suggested_cards_count: int = Field(
        description="Quantidade sugerida de cartões de estudo para cobrir os temas."
    )
    rationale: str = Field(
        description="Explicação sucinta sobre o porquê da contagem sugerida."
    )


class Flashcard(BaseModel):
    question: str = Field(
        description="A pergunta clara e concisa a ser colocada no anverso do cartão."
    )
    answer_text: str = Field(
        description="A resposta direta e objetiva para o verso do cartão."
    )
    source_reference: str = Field(
        description="Referência precisa do trecho (Ex: URL com timestamp para YouTube)."
    )


class FlashcardCollection(BaseModel):
    cards: list[Flashcard]
