# Guia de Integração com a API do Gemini (GEMINI.md)

Este documento centraliza as diretrizes técnicas para o consumo das APIs do Google Gemini no projeto `anki_generator` utilizando o SDK oficial `google-genai`.

---

## 1. Modelos Utilizados

A pipeline utiliza dois modelos distintos para processamento de texto e síntese de voz:

| Função | Identificador do Modelo (ID) | Modos de Entrada/Saída |
| :--- | :--- | :--- |
| **Geração de Texto e Análise** | `gemini-3.5-flash` | Entrada: Texto (ou Multimodal) / Saída: Texto (JSON Estruturado) |
| **Síntese de Voz (TTS)** | `gemini-3.1-flash-tts-preview` | Entrada: Texto / Saída: Áudio (PCM Bruto) |

---

## 2. Autenticação e Configuração

*   **Variável de Ambiente:** A autenticação é realizada unicamente por meio da variável `GEMINI_API_KEY`.
*   **Carregamento de Configurações:** O SDK lê automaticamente o valor da chave através do construtor padrão `genai.Client()`. Na aplicação, as configurações são gerenciadas pela biblioteca `pydantic-settings`.

### Configuração Recomendada (.env)
```env
GEMINI_API_KEY="AIzaSyYourActualApiKeyHere"
```

---

## 3. Padrões de Uso do SDK

### A. Geração Estruturada (Modelo de Texto)
Para garantir que a saída de geração de temas e cartões respeite os schemas rígidos definidos, o SDK utiliza parâmetros de configuração em JSON.

```python
from google import genai
from anki_generator.models import FlashcardCollection

client = genai.Client()

response = client.models.generate_content(
    model="gemini-3.5-flash",
    contents="Prompt estruturado com o material de estudos.",
    config={
        "response_mime_type": "application/json",
        "response_schema": FlashcardCollection,
    }
)

# O atributo parsed contém a instância do Pydantic validada
flashcards = response.parsed
```

### B. Síntese de Voz (TTS)
O modelo `gemini-3.1-flash-tts-preview` gera áudio em resposta a comandos textuais. A resposta deve ser explicitamente configurada para áudio.

```python
from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
    model="gemini-3.1-flash-tts-preview",
    contents="Texto a ser convertido em voz.",
    config=types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name="Kore"
                )
            )
        )
    )
)

# Os bytes de áudio bruto estão contidos na resposta
raw_pcm_bytes = response.candidates[0].content.parts[0].inline_data.data
```

---

## 4. Limites de Requisições e Erros (Rate Limits)

*   **HTTP 429 (Too Many Requests):** Ocorre quando os limites de requisições por minuto (RPM) ou tokens por minuto (TPM) da chave de API são atingidos.
*   **Mitigação:** Implementa-se uma camada de persistência com retentativas baseadas na biblioteca `tenacity`, utilizando recuo exponencial para evitar congestionar as APIs.

### Estratégia de Retentativas
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def generate_content_with_retry(client, model, contents, config):
    return client.models.generate_content(model=model, contents=contents, config=config)
```
