# Guia de Integração com a API do Gemini (GEMINI.md)

Este documento centraliza as diretrizes técnicas e as configurações definitivas utilizadas para o consumo das APIs do Google Gemini no projeto `anki_generator` por meio do SDK oficial `google-genai`.

---

## 1. Modelos e Configurações de Mídia

A pipeline utiliza dois modelos distintos para processamento de texto e síntese de voz:

| Função | Identificador do Modelo (ID) | Modos de Entrada/Saída |
| :--- | :--- | :--- |
| **Geração de Texto e Análise** | `gemini-3.5-flash` | Entrada: Texto / Saída: Texto (JSON Estruturado) |
| **Síntese de Voz (TTS)** | `gemini-3.1-flash-tts-preview` | Entrada: Texto / Saída: Áudio (PCM Bruto 16-bit 24kHz) |

---

## 2. Autenticação e Configuração

*   **Variável de Ambiente:** A autenticação é realizada unicamente por meio da variável `GEMINI_API_KEY`.
*   **Carregamento de Configurações:** O SDK lê automaticamente o valor da chave através do construtor padrão `genai.Client()`. Na aplicação, as configurações são gerenciadas pela biblioteca `pydantic-settings`.

### Configuração Recomendada (.env)
```env
GEMINI_API_KEY="AIzaSyYourActualApiKeyHere"
```

---

## 3. Padrões de Uso do SDK (`google-genai==0.8.0`)

### A. Geração Estruturada (Modelo de Texto)
Para garantir que a saída de geração de temas e cartões respeite os schemas rígidos definidos de forma consistente e com alto determinismo, o SDK utiliza parâmetros de configuração em JSON com a estrutura do Pydantic v2 e define a **temperatura explicitamente em 0.1**.

```python
from google import genai
from google.genai import types
from anki_generator.models import FlashcardCollection

client = genai.Client()

config = types.GenerateContentConfig(
    response_mime_type="application/json",
    response_schema=FlashcardCollection,
    temperature=0.1,
)

response = client.models.generate_content(
    model="gemini-3.5-flash",
    contents="Prompt estruturado com o material de estudos.",
    config=config
)

# O atributo parsed contém a instância do Pydantic validada
flashcards = response.parsed
```

### B. Síntese de Voz (TTS) com Mapeamento Dinâmico de Vozes
O modelo `gemini-3.1-flash-tts-preview` gera áudio em resposta a comandos textuais. A voz de resposta é mapeada de acordo com o idioma selecionado na interface de terminal (CLI):

*   **Português (PT):** Voz `Fenrir`
*   **Inglês (EN):** Voz `Kore`
*   **Espanhol (ES):** Voz `Aoede`
*   **Outros/Fallback:** Voz `Kore`

```python
from google import genai
from google.genai import types

client = genai.Client()

config = types.GenerateContentConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name="Fenrir"  # Mapeado dinamicamente
            )
        )
    )
)

response = client.models.generate_content(
    model="gemini-3.1-flash-tts-preview",
    contents="Texto a ser convertido em voz.",
    config=config
)

# Os bytes de áudio bruto (PCM) estão contidos na resposta
raw_pcm_bytes = response.candidates[0].content.parts[0].inline_data.data
```

### C. Pré-Análise de Conteúdo e Recomendação de Contagem
Para sugerir temas e um número ideal de cartões de estudo a partir dos materiais de entrada (seja no fluxo interativo ou quando a contagem é omitida no modo scriptável), a pipeline utiliza uma chamada estruturada com o schema `ThemeSuggestion` e temperatura `0.1`.

```python
from google import genai
from google.genai import types
from anki_generator.models import ThemeSuggestion

client = genai.Client()

config = types.GenerateContentConfig(
    response_mime_type="application/json",
    response_schema=ThemeSuggestion,
    temperature=0.1,
)

response = client.models.generate_content(
    model="gemini-3.5-flash",
    contents="Texto do material de estudos.",
    config=config
)

# O atributo parsed contém a sugestão de temas e contagem validada
suggestion = response.parsed
```

---


## 4. Limites de Requisições e Erros (Rate Limits)

*   **HTTP 429 (Too Many Requests):** Ocorre quando os limites de requisições por minuto (RPM) ou tokens por minuto (TPM) da chave de API são atingidos.
*   **Mitigação:** Implementa-se uma camada de persistência com retentativas baseadas na biblioteca `tenacity`, utilizando recuo exponencial para evitar congestionar as APIs.

### Estratégia de Retentativas Implementada
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
