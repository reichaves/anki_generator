# Especificação Técnica (Spec.md) — Pipeline `anki_generator`

Plano de implementação tático, arquitetura de testes, regras de negócio e segurança para a
pipeline em Python `anki_generator`: ingere `.docx`, `.pdf` e transcrições de YouTube, gera
cartões de estudo do Anki (pergunta → resposta) via Gemini, com áudio opcional da resposta via
TTS, e exporta para o Anki (`genanki` por padrão ou `AnkiConnect` opcional).

> Esta versão corrige bloqueadores e lacunas da revisão técnica. Ver **§11 Changelog**.

---

## 1. Stack Técnica e Dependências

| Dependência | Versão | Justificativa |
| :--- | :--- | :--- |
| **Python** | `>= 3.12` | Tipagem moderna e melhorias de performance. |
| **google-genai** | `>= 2.9, < 3` | SDK oficial atual do Gemini (texto + TTS). `0.1.x` é stale e não tem a API usada. |
| **genanki** | `>= 0.13, < 1` | Geração offline do `.apkg`. |
| **youtube-transcript-api** | `>= 0.6, < 1` | Transcrição com timestamps do YouTube. |
| **python-docx** | `>= 1.1, < 2` | Leitura de `.docx`. |
| **pypdf** | `>= 4.2, < 6` | Extração de texto local de PDF. |
| **httpx** | `>= 0.27` | Cliente HTTP do AnkiConnect (consistente com `respx`; já é dep transitiva do `google-genai`). |
| **pydantic** | `>= 2.6, < 3` | Schemas e validação estrita. |
| **pydantic-settings** | `>= 2.2, < 3` | Configuração e chave de API via ambiente. |
| **tenacity** | `>= 8.2, < 10` | Recuo exponencial para erros `429`. |
| **structlog** | `>= 24.1` | Logs estruturados. |
| **questionary** | `>= 2.0, < 3` | Diálogo interativo da CLI. |
| **rich** | `>= 13.7` | Formatação, tabelas e barra de progresso. |
| **pytest** | `>= 8.1` | Framework de testes. |
| **pytest-mock** | `>= 3.14` | Mocks de funções/objetos. |
| **pytest-cov** | `>= 5.0` | Medição de cobertura (gate ≥ 80%). |
| **respx** | `>= 0.21` | Mock de HTTP `httpx` (AnkiConnect). |
| **ruff** | `>= 0.4` | Lint + format. |
| **mypy** | `>= 1.9` | Type checking estrito. |

> **Nota:** `requests` foi removido — o AnkiConnect usa `httpx` para que `respx` possa
> interceptar as chamadas nos testes.

---

## 2. Estrutura de Diretórios

```
anki_generator/
├── content/
│   └── .gitkeep                  # usuário deposita .docx/.pdf aqui
├── results/
│   ├── .gitkeep                  # saída: .apkg, mídia e resumo de execução
│   └── media/                    # (criado em runtime) .wav gerados
├── references/
│   ├── architecture.md
│   ├── design.md
│   ├── specification.md
│   ├── workflow.md
│   └── constitution.md
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # fixtures compartilhadas (.docx/.pdf, mocks)
│   ├── fixtures/
│   │   ├── sample.docx
│   │   └── sample.pdf
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_config.py
│   │   ├── test_models.py
│   │   ├── test_extractors.py
│   │   ├── test_gemini_client.py
│   │   ├── test_anki_exporter.py
│   │   └── test_cli.py
│   └── integration/
│       ├── __init__.py
│       └── test_pipeline.py
├── anki_generator/
│   ├── __init__.py               # __all__ com exportações públicas
│   ├── config.py
│   ├── exceptions.py
│   ├── models.py
│   ├── extractors.py
│   ├── gemini_client.py
│   ├── anki_exporter.py
│   └── cli.py
├── .env.example
├── .gitignore
├── main.py
├── pyproject.toml                # configuração de ruff, mypy, pytest, coverage
├── requirements.txt              # dependências fixadas
├── README.md
├── PRD.md
└── Spec.md
```

---

## 3. Manifesto de Arquivos

| Caminho | Justificativa |
| :--- | :--- |
| `content/.gitkeep` | Mantém o diretório de entrada rastreado e vazio no git. |
| `results/.gitkeep` | Mantém o diretório de saída rastreado e vazio no git. |
| `references/*.md` | Documentação de arquitetura, design, regras, workflow e constituição. |
| `.gitignore` | Ignora `.env`, dados do usuário e caches. |
| `.env.example` | Modelo das variáveis de ambiente. |
| `pyproject.toml` | Configuração centralizada de ruff, mypy (strict), pytest e coverage. |
| `requirements.txt` | Dependências fixadas para reprodutibilidade. |
| `README.md` | Quickstart: instalar, configurar `.env`, depositar arquivos, executar, ver saída. |
| `main.py` | Ponto de entrada; importa e dispara a CLI. |
| `anki_generator/__init__.py` | Barrel export (`__all__`). |
| `anki_generator/config.py` | Configuração via `pydantic-settings`; falha explícita sem a chave. |
| `anki_generator/exceptions.py` | Exceções de domínio para tratamento limpo na CLI. |
| `anki_generator/models.py` | Schemas Pydantic (contratos de dados). |
| `anki_generator/extractors.py` | Extração de `.docx`, `.pdf` e YouTube (com validação de URL). |
| `anki_generator/gemini_client.py` | Cliente Gemini: sugestão de temas, geração de cartões e TTS. |
| `anki_generator/anki_exporter.py` | Exporta `.apkg` (genanki) ou via AnkiConnect, com mídia. |
| `anki_generator/cli.py` | Diálogo interativo (`questionary` + `rich`) e orquestração. |

### `.gitignore`
```
# Ambiente
.env

# Dados locais do usuário (ignora conteúdo, mantém .gitkeep)
content/*
!content/.gitkeep
results/*
!results/.gitkeep

# Caches e builds
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
build/
dist/
*.egg-info/
```

### `.env.example`
```
# Obrigatória — chave da API do Gemini
GEMINI_API_KEY=your_api_key_here

# Opcionais
ANKI_CONNECT_URL=http://localhost:8765
DEFAULT_TTS_VOICE=Kore
```

### `pyproject.toml` (configuração de ferramentas)
```toml
[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "ANN", "SIM", "PTH"]

[tool.mypy]
python_version = "3.12"
strict = true
warn_unused_ignores = true
disallow_any_generics = true

[tool.pytest.ini_options]
addopts = "--cov=anki_generator --cov-report=term-missing --cov-fail-under=80"
testpaths = ["tests"]

[tool.coverage.run]
source = ["anki_generator"]
branch = true
```

---

## 4. Explicação de Arquivos e Snippets

### A. `anki_generator/exceptions.py`
Exceções de domínio. A CLI as captura e exibe mensagem clara (sem stack trace cru).
```python
class AnkiGeneratorError(Exception):
    """Base para erros do projeto."""

class ConfigError(AnkiGeneratorError):
    """Configuração/credenciais ausentes ou inválidas."""

class ExtractionError(AnkiGeneratorError):
    """Falha ao extrair conteúdo de uma fonte (docx/pdf/URL inválida)."""

class TranscriptUnavailableError(ExtractionError):
    """Vídeo do YouTube sem legenda disponível."""

class GeminiError(AnkiGeneratorError):
    """Falha na chamada ou no parsing da resposta do Gemini."""

class ExportError(AnkiGeneratorError):
    """Falha ao exportar para o Anki (genanki/AnkiConnect)."""
```

### B. `anki_generator/config.py`
Carrega configuração via `pydantic-settings`. O campo `gemini_api_key` casa automaticamente
com a env `GEMINI_API_KEY` (case-insensitive) — **sem `alias`** para evitar bug de carga.
```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import ValidationError

from anki_generator.exceptions import ConfigError


class Settings(BaseSettings):
    gemini_api_key: str = Field(..., min_length=1)
    anki_connect_url: str = "http://localhost:8765"
    default_tts_voice: str = "Kore"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )


def load_settings() -> Settings:
    try:
        return Settings()  # type: ignore[call-arg]
    except ValidationError as exc:
        raise ConfigError("GEMINI_API_KEY ausente ou inválida no ambiente/.env.") from exc
```

### C. `anki_generator/models.py`
Contratos rígidos com Pydantic v2.
```python
from enum import Enum
from pydantic import BaseModel, Field


class CardModality(str, Enum):
    TEXT_ONLY = "text_only"
    TEXT_AUDIO = "text_audio"


class ThemeSuggestion(BaseModel):
    themes: list[str] = Field(description="Temas/tópicos identificados no material.")
    suggested_cards_count: int = Field(ge=1, description="Quantidade sugerida de cartões.")
    rationale: str = Field(description="Justificativa sucinta da contagem.")


class Flashcard(BaseModel):
    question: str = Field(description="Pergunta clara e concisa (anverso).")
    answer_text: str = Field(description="Resposta direta e objetiva (verso).")
    source_reference: str = Field(description="Fonte (ex.: URL do YouTube com timestamp).")


class FlashcardCollection(BaseModel):
    cards: list[Flashcard]


class RunSummary(BaseModel):
    sources: list[str]
    language: str
    modality: CardModality
    cards_requested: int
    cards_generated: int
    apkg_path: str | None
    warnings: list[str] = Field(default_factory=list)
```

### D. `anki_generator/extractors.py`
Funções para `.docx` (`python-docx`), `.pdf` (`pypdf` local; fallback multimodal via Files API
documentado como opção) e YouTube.
- **Validação de URL do YouTube:** extrair o ID com regex; URL inválida → `ExtractionError`.
- **Timestamp:** para cada trecho com `start`/`text`, mapear `int(start)` e anexar `&t=NNNs` à
  URL base, compondo a `source_reference` do cartão.
- **Erro de legenda:** ausência de transcrição → `TranscriptUnavailableError`.
```python
import re
from anki_generator.exceptions import ExtractionError

_YT_ID = re.compile(r"(?:v=|/shorts/|youtu\.be/)([A-Za-z0-9_-]{11})")

def extract_youtube_id(url: str) -> str:
    match = _YT_ID.search(url)
    if not match:
        raise ExtractionError(f"URL do YouTube inválida: {url!r}")
    return match.group(1)
```

### E. `anki_generator/gemini_client.py`
Orquestra o Gemini com o SDK `google-genai`. **Tratamento defensivo obrigatório** das respostas.
Retentativas com `tenacity` para `429`.

- **Sugestão de temas/quantidade** (`response_schema=ThemeSuggestion`).
- **Geração de cartões** respeitando idioma e número pedido:
```python
parsed = response.parsed
if parsed is None:
    raise GeminiError("Resposta do Gemini não pôde ser parseada como JSON estruturado.")
collection = FlashcardCollection.model_validate(parsed)
```
- **TTS + conversão PCM→WAV** com verificação de payload e nome de arquivo por hash:
```python
import hashlib, wave
from anki_generator.exceptions import GeminiError

def _safe_audio_name(text: str) -> str:
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]
    return f"audio_{digest}.wav"

part = response.candidates[0].content.parts[0]
pcm = getattr(part.inline_data, "data", None)
if not pcm:
    raise GeminiError("TTS retornou áudio vazio.")

def write_wav(path: str, pcm: bytes, *, channels: int = 1, rate: int = 24000, width: int = 2) -> None:
    with wave.open(path, "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(width)
        wav.setframerate(rate)
        wav.writeframes(pcm)
```
- **Voz/idioma:** voz default vem de `settings.default_tts_voice` (não fixar cega no código);
  documentar em `references/design.md` a relação voz × idioma.

### F. `anki_generator/anki_exporter.py`
- **genanki (padrão):** `Model` com IDs fixos (estáveis entre execuções), campos
  `Question / AnswerText / Audio / Source`. No modo texto+áudio, o campo `Audio` recebe
  `[sound:audio_<hash>.wav]` e o `.wav` entra em `media_files`. No modo **apenas texto**, o
  campo `Audio` fica vazio e nenhum `.wav` é gerado/anexado.
- **Nome do pacote com timestamp:** `results/anki_<deck>_<YYYYMMDD-HHMMSS>.apkg` (não
  sobrescreve execuções anteriores).
- **AnkiConnect (opcional):** `storeMediaFile` (base64) + `addNote` via `httpx` para
  `settings.anki_connect_url`. Erros HTTP → `ExportError`.
- **Limpeza:** após escrever o `.apkg`, os `.wav` temporários ficam em `results/media/`
  (mantidos para auditoria); documentar esse comportamento no README.

---

## 5. Fluxo de Execução Interativo (UX)

Ao rodar `python main.py`:

1. **Escaneamento de fontes.** A CLI mapeia `content/` por `.docx`/`.pdf` e apresenta seleção
   múltipla (`questionary.checkbox`, opção "todos"). O usuário pode também informar uma ou mais
   URLs do YouTube. Exige ao menos uma fonte; caso contrário, aborta com mensagem `rich`.
2. **Extração.** Lê o conteúdo das fontes escolhidas (com barra de progresso). URLs inválidas ou
   vídeos sem legenda geram aviso claro.
3. **Pré-análise e sugestão.** Chamada ao Gemini (`ThemeSuggestion`) exibe, via `rich.table`,
   os temas encontrados e um número sugerido de cartões.
4. **Configuração do usuário (prompts):**
   - *Quantidade de cartões* — inteiro positivo, default = sugestão do passo 3.
   - *Idioma de saída* — governa pergunta, resposta e o texto enviado ao TTS.
   - *Modalidade* — "Apenas texto" ou "Texto + Áudio" (texto pula totalmente o TTS).
5. **Geração.** Gera os cartões respeitando idioma e quantidade. **Regra anti-alucinação:** se o
   material render menos cartões com qualidade do que o pedido, o sistema **avisa** e gera o
   máximo coerente — nunca inventa conteúdo para bater o número. Se for texto+áudio, sintetiza
   o `.wav` de cada resposta.
6. **Exportação e resumo.** Empacota em `results/anki_<deck>_<timestamp>.apkg` (ou injeta via
   AnkiConnect), salva `results/run_<YYYYMMDD-HHMMSS>.json` (modelo `RunSummary`: fontes,
   idioma, modalidade, pedido vs gerado, caminho do `.apkg`, avisos) e exibe um resumo final
   formatado no terminal.

---

## 6. Estratégia de Mocks e Testes

Nenhum teste faz chamada de rede real.

### Mocks obrigatórios
- **google-genai:** mockar `client.models.generate_content` (temas, cartões e TTS) e
  `client.files.upload`, retornando objetos que mimetizam `.parsed` e o `inline_data.data`
  binário (PCM). Testar também `parsed is None` → `GeminiError`.
- **AnkiConnect:** mockar `http://localhost:8765` com `respx` (sucesso e falha de conexão).
- **youtube-transcript-api:** simular lista de trechos (`start`/`text`); testar
  `TranscriptsDisabled` → `TranscriptUnavailableError`.
- **CLI:** `unittest.mock`/`pytest-mock` sobre os prompts do `questionary` para simular escolhas.

### Cenários por arquivo
- `test_config.py` — ausência de `GEMINI_API_KEY` → `ConfigError`; defaults aplicados.
- `test_models.py` — validação de `Flashcard`, `FlashcardCollection`, `ThemeSuggestion`,
  `RunSummary`; rejeição de `suggested_cards_count < 1`.
- `test_extractors.py` — leitura de `.docx`/`.pdf` (fixtures); `extract_youtube_id` com URLs
  válidas/ inválidas; montagem de `&t=NNNs`; legenda ausente → `TranscriptUnavailableError`.
- `test_gemini_client.py` — parsing sob `FlashcardCollection`; `parsed is None` → `GeminiError`;
  TTS com payload vazio → `GeminiError`; escrita do `.wav` a partir de PCM mockado; nome por hash.
- `test_anki_exporter.py` — `.apkg` gerado em `results/` com nome timestampado; `media_files`
  contém o `.wav` no modo texto+áudio e **não** contém no modo apenas texto; falha HTTP do
  AnkiConnect → `ExportError`.
- `test_cli.py` — fluxo interativo simulado; nenhuma fonte → aborta com mensagem; quantidade
  inválida rejeitada; **gerar menos cartões que o pedido emite aviso** (sem inventar).
- `integration/test_pipeline.py` — pipeline ponta a ponta com todos os mocks e inputs simulados,
  produzindo `.apkg` e `run_<timestamp>.json` em `results/`.

---

## 7. Segurança e Práticas

- **Credenciais:** somente via ambiente (`pydantic-settings`); nunca em código ou docs.
- **Logs sanitizados:** `structlog` nunca registra a chave nem o áudio bruto/base64; conteúdo de
  transcrição é truncado.
- **Path traversal:** caminhos lidos da CLI devem resolver estritamente dentro de `content/`
  (validar com `Path.resolve()` e checar prefixo). Saída exclusivamente em `results/`.
- **URLs:** IDs de YouTube validados por regex antes do processamento.
- **Sem `eval`/`exec`** nem execução dinâmica de código.

---

## 8. Referências (`references/`)

- **architecture.md** — limites do sistema batch, modularização, fluxo de dados, mapa de
  dependências; acoplamento CLI↔lógica evitado via API interna dos módulos.
- **design.md** — UX/UI da CLI: cada prompt (texto, tipo, default, validação), mensagens de
  erro acionáveis, spinners/progresso, tabela de resumo; relação **voz × idioma** do TTS;
  contrato de entrada (`content/`) e saída (`results/`).
- **specification.md** — schemas Pydantic, contratos com Gemini e AnkiConnect, **regras de
  negócio**: idioma governando pergunta/resposta/TTS; respeitar a quantidade pedida sem
  alucinar; modalidade texto/áudio; formato `[sound:...]`; montagem de timestamp.
- **workflow.md** — ciclo SDD; testes antes do código; rodar `ruff`/`mypy`/`pytest`+cobertura;
  git flow; execução local.
- **constitution.md** — regras inegociáveis: segurança por padrão; tipagem estrita; testes antes
  do merge; `ruff`/`mypy` verdes como gate; sem chave/áudio em logs; simplicidade; CLI sem
  lógica de negócio; saída restrita a `results/`.

---

## 9. Plano de Implementação (Milestones)

```
M1: Config & Contratos ─> M2: Extratores ─> M3: Gemini Client
                                                   │
M5: CLI & Integração  <─ M4: Anki Exporter  <──────┘
```

Quality gates de **todos** os milestones: `ruff check .` e `ruff format --check .` = 0;
`mypy anki_generator` (strict) = 0; `pytest` 100% verde; cobertura ≥ 80%
(`--cov-fail-under=80`); nenhuma credencial hardcoded.

### M1 — Configuração, Ambiente e Contratos
- **Entregáveis:** `pyproject.toml`, `requirements.txt`, `.gitignore`, `.env.example`,
  `anki_generator/exceptions.py`, `anki_generator/config.py`, `anki_generator/models.py`,
  diretórios `content/`/`results/` com `.gitkeep`, `README.md` (quickstart).
- **Aceitação:** `test_config.py` e `test_models.py` verdes; ausência de chave → `ConfigError`.

### M2 — Extratores
- **Entregáveis:** `anki_generator/extractors.py`, fixtures `.docx`/`.pdf` em `tests/fixtures/`.
- **Aceitação:** extrai texto de `.docx`/`.pdf`; `extract_youtube_id` valida URLs; timestamp
  `&t=NNNs` correto; legenda ausente → `TranscriptUnavailableError`.

### M3 — Gemini Client
- **Entregáveis:** `anki_generator/gemini_client.py`.
- **Aceitação:** sugestão de temas e geração de cartões (JSON validado, idioma/quantidade
  respeitados); TTS gera `.wav` PCM 16-bit/24kHz com nome por hash; tratamento defensivo
  (`parsed is None`, áudio vazio) → `GeminiError`; retentativa com `tenacity` para `429`.

### M4 — Anki Exporter
- **Entregáveis:** `anki_generator/anki_exporter.py`.
- **Aceitação:** `.apkg` timestampado em `results/`; `media_files` com áudio no modo
  texto+áudio e vazio no modo apenas texto; AnkiConnect mockado via `respx`; falha → `ExportError`.

### M5 — CLI Interativa e Integração
- **Entregáveis:** `anki_generator/cli.py`, `main.py`, `tests/integration/test_pipeline.py`,
  `references/*.md`.
- **Aceitação:** diálogo completo (seleção, sugestão, quantidade, idioma, modalidade); aviso ao
  gerar menos que o pedido; integração ponta a ponta gera `.apkg` + `run_<timestamp>.json` em
  `results/`.

---

## 10. Non-Goals (Fora de Escopo)

- GUI ou aplicação web.
- Agendamento automatizado (cron/triggers).
- Geração/processamento de imagens ou outras mídias não especificadas.
- Deduplicação semântica ou comparação com cartões já existentes no Anki do usuário.
- Edição/revisão manual dos textos dos cartões dentro do fluxo.
- Fontes além de `.docx`/`.pdf`/YouTube nesta fase.

---

## 11. Changelog (correções desta revisão)

1. **`google-genai`** corrigido de `== 0.1.1` para `>= 2.9, < 3` (versão atual; a antiga não tem
   a API usada nos snippets).
2. **AnkiConnect** migrado de `requests` para **`httpx`**, para compatibilizar com `respx` nos
   testes; `requests` removido das dependências.
3. **`pytest-cov`** adicionado; gates de cobertura via `--cov-fail-under=80`.
4. **`pyproject.toml`** adicionado para configurar `ruff`, `mypy` (strict), `pytest` e coverage.
5. **`README.md`** adicionado como entregável (quickstart).
6. **`exceptions.py`** adicionado com taxonomia de erros de domínio.
7. **Tratamento defensivo das respostas do Gemini** (`parsed is None`; áudio vazio) → `GeminiError`.
8. **`config.py` simplificado** (sem `alias` problemático; falha explícita via `ConfigError`).
9. **Regra anti-alucinação de quantidade** reintroduzida (respeitar o pedido; avisar se render
   menos; nunca inventar) + teste.
10. **Resumo persistido** `results/run_<timestamp>.json` (modelo `RunSummary`).
11. **Nomes de mídia por hash** (`audio_<sha1[:12]>.wav`) para casar com `[sound:...]` e evitar
    colisões.
12. **`.apkg` timestampado** para não sobrescrever execuções anteriores.
13. **Política de limpeza** dos `.wav` (mantidos em `results/media/`) definida.
14. **Voz do TTS configurável** (`default_tts_voice`) e relação voz × idioma documentada.
15. **Validação de URL do YouTube** por regex → `ExtractionError`.
