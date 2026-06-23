# Estado do Projeto: anki_generator

## Resumo
Projeto de pipeline interativa em Python que ingere documentos DOCX, PDF e transcrições do YouTube, gera cartões de estudo com a API do Gemini (`gemini-3.5-flash`) com suporte opcional a áudio (TTS via `gemini-3.1-flash-tts-preview`) e os exporta para o Anki (offline via `genanki` por padrão ou online via `AnkiConnect`).

## Stack Principal
- Python 3.14+
- `google-genai==0.8.0`
- `genanki==0.13.0`
- `youtube-transcript-api==0.6.2`
- `python-docx==1.1.0`
- `pypdf==4.2.0`
- `requests==2.31.0`
- `pydantic==2.12.0`
- `pydantic-settings==2.12.0`
- `pytest-cov==4.1.0`

## Status dos Milestones
- **M1: Config & Contratos**: Concluído (Testes unitários verdes, cobertura 100%, Ruff/Mypy OK).
- **M2: Extractors**: Não Iniciado.
- **M3: Gemini Client**: Não Iniciado.
- **M4: Anki Exporter**: Não Iniciado.
- **M5: CLI & Integração**: Não Iniciado.
