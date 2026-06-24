# Estado do Projeto: anki_generator

## Resumo
Projeto de pipeline interativa em Python que ingere documentos DOCX, PDF e transcrições do YouTube, gera cartões de estudo com a API do Gemini (`gemini-3.5-flash`) com suporte opcional a áudio (TTS via `gemini-3.1-flash-tts-preview`) e os exporta para o Anki (offline via `genanki` por padrão ou online via `AnkiConnect`).

## Stack Principal
- Python 3.14+
- `google-genai==0.8.0`
- `genanki==0.13.0`
- `youtube-transcript-api==1.2.4`
- `python-docx==1.1.0`
- `pypdf==4.2.0`
- `requests==2.31.0`
- `pydantic==2.12.0`
- `pydantic-settings==2.12.0`
- `pytest-cov==4.1.0`

## Status dos Milestones
- **M1: Config & Contratos**: Concluído (Testes unitários verdes, cobertura 100%, Ruff/Mypy OK).
- **M2: Extractors**: Concluído (Testes unitários verdes, cobertura 96%, Ruff/Mypy OK).
- **M3: Gemini Client**: Concluído (Testes unitários verdes, cobertura 95%, Ruff/Mypy OK).
- **M4: Anki Exporter**: Concluído (Testes unitários verdes, cobertura 89%, Ruff/Mypy OK).
- **M5: CLI & Integração**: Concluído (Testes unitários/integração verdes, cobertura 72% localmente/86% global, Ruff/Mypy OK).
- **Empacotamento e Distribuição**: Concluído (pyproject.toml configurado, comando global anki-generator ativado via pip).
- **Recursos Adicionais**: Seleção de nome customizado do baralho (deck) do Anki na CLI, configuração de "Type-in-the-Answer" (resposta digitada) no template dos cartões gerados, e fallback automático de exportação offline (.apkg) em caso de falha de conexão do AnkiConnect. Cobertura de testes global em 86.56%, com Ruff e Mypy 100% OK.

## Pull Requests Avaliados e Mesclados (Junho 2026)
* **PR #1 - fix(exporter): derive deterministic deck IDs from a stable hash**: Resolvido o problema de IDs voláteis de baralho gerados via `hash()`. Substituído por `stable_deck_id()` baseado em SHA-256 estável para garantir reimportações idempotentes no Anki. (Ver: [pr1_analysis_report.md](file:///C:/Users/User/.gemini/antigravity-cli/brain/a1507857-dabc-4bed-b426-a632631075b6/pr1_analysis_report.md)).
* **PR #2 - feat(cli): add non-interactive (scriptable) mode**: Implementadas as flags via `argparse` no CLI despachante `main()`, permitindo automação da pipeline. Lógica refatorada em utilitários de extração e exportação reutilizáveis. Ponto de entrada secundário em `__main__.py` também atualizado para compatibilidade. (Ver: [pr2_analysis_report.md](file:///C:/Users/User/.gemini/antigravity-cli/brain/a1507857-dabc-4bed-b426-a632631075b6/pr2_analysis_report.md)).

