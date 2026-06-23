import os
import wave
import structlog
from google import genai  # type: ignore[import-untyped]
from google.genai import types  # type: ignore[import-untyped]
from tenacity import retry, stop_after_attempt, wait_exponential
from anki_generator.config import settings
from anki_generator.models import ThemeSuggestion, FlashcardCollection

logger = structlog.get_logger()


def get_voice_for_language(language: str) -> str:
    """Retorna o nome da voz pré-configurada do Gemini com base no idioma."""
    lang_clean = language.strip().lower()
    if "portug" in lang_clean or lang_clean == "pt":
        return "Fenrir"
    elif "ingl" in lang_clean or "english" in lang_clean or lang_clean == "en":
        return "Kore"
    elif "espan" in lang_clean or "spanish" in lang_clean or lang_clean == "es":
        return "Aoede"
    return "Kore"


def save_pcm_as_wav(
    output_path: str,
    pcm_data: bytes,
    channels: int = 1,
    rate: int = 24000,
    sample_width: int = 2,
) -> None:
    """Converte dados brutos PCM obtidos do Gemini TTS em um arquivo WAV estruturado."""
    logger.info("Salvando arquivo WAV", path=output_path)
    try:
        parent_dir = os.path.dirname(output_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        with wave.open(output_path, "wb") as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(rate)
            wav_file.writeframes(pcm_data)
    except Exception as e:
        logger.error("Erro ao salvar arquivo WAV", error=str(e), path=output_path)
        raise IOError(f"Falha ao gravar arquivo de áudio WAV: {e}") from e


class GeminiClient:
    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or settings.gemini_api_key
        self.client = genai.Client(api_key=key)

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def _generate_with_retry(
        self,
        model: str,
        contents: str,
        config: types.GenerateContentConfig,
    ) -> types.GenerateContentResponse:
        logger.info("Enviando requisição para o Gemini", model=model)
        return self.client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )

    def suggest_themes(self, text: str) -> ThemeSuggestion:
        """Sugere temas e quantidade recomendada de cartões a partir de um texto."""
        prompt = (
            "Analise o texto abaixo e identifique os principais temas/tópicos abordados. "
            "Sugira uma quantidade coerente de cartões de estudo (flashcards) para cobrir "
            "o conteúdo de forma abrangente sem repetição. Forneça uma justificativa rápida.\n\n"
            f"Texto:\n{text}"
        )
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ThemeSuggestion,
            temperature=0.1,
        )
        response = self._generate_with_retry(
            model="gemini-3.5-flash",
            contents=prompt,
            config=config,
        )
        parsed: ThemeSuggestion = response.parsed
        return parsed

    def generate_flashcards(
        self, text: str, count: int, language: str
    ) -> FlashcardCollection:
        """Gere uma coleção estruturada de cartões de estudo a partir de um texto no idioma selecionado."""
        prompt = (
            f"Gere exatamente {count} cartões de estudo (flashcards) com base no texto abaixo.\n"
            f"Cada cartão deve estar no formato pergunta -> resposta.\n"
            f"Tanto a pergunta quanto a resposta devem ser geradas em {language}.\n"
            "Selecione as informações mais importantes e evite duplicações.\n"
            "No campo 'source_reference', aponte de onde veio a informação. Se houver timestamps do YouTube (ex: &t=NNNs), insira a URL completa com o timestamp correspondente.\n\n"
            f"Texto:\n{text}"
        )
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=FlashcardCollection,
            temperature=0.1,
        )
        response = self._generate_with_retry(
            model="gemini-3.5-flash",
            contents=prompt,
            config=config,
        )
        parsed: FlashcardCollection = response.parsed
        return parsed

    def generate_audio(self, text: str, language: str) -> bytes:
        """Invoca o modelo TTS do Gemini e retorna os bytes brutos do áudio PCM."""
        voice = get_voice_for_language(language)
        logger.info("Gerando áudio via TTS", voice=voice, language=language)

        config = types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                )
            ),
        )
        response = self._generate_with_retry(
            model="gemini-3.1-flash-tts-preview",
            contents=text,
            config=config,
        )

        try:
            raw_pcm: bytes = response.candidates[0].content.parts[0].inline_data.data
            return raw_pcm
        except (IndexError, AttributeError) as e:
            logger.error(
                "Falha ao extrair dados de áudio da resposta do Gemini", error=str(e)
            )
            raise RuntimeError(
                "Nenhum dado de áudio foi retornado pela API do Gemini."
            ) from e
