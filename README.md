# anki_generator - Gerador de Flashcards via Gemini

Pipeline automatizada e interativa em Python que ingere documentos Word (`.docx`), PDFs (`.pdf`) e URLs de vídeos do YouTube para gerar cartões de estudo (flashcards) para o Anki no formato pergunta/resposta com suporte a áudio (TTS).

---

## 1. Stack Tecnológica
*   **Python:** `>= 3.12` (Testado e validado em CPython 3.14)
*   **APIs do Gemini:** `gemini-3.5-flash` (Texto/JSON estruturado) e `gemini-3.1-flash-tts-preview` (Áudio/TTS)
*   **Exportação do Anki:** `genanki` (Geração offline de pacotes `.apkg`) e `AnkiConnect` (Injeção de notas via HTTP local)
*   **Extratores:** `python-docx` para Word, `pypdf` para PDFs locais e `youtube-transcript-api` para transcrições do YouTube

---

## 2. Instalação e Preparação

### Configuração do Ambiente

1.  Crie e ative seu ambiente virtual:
    ```bash
    python -m venv .venv
    .venv\Scripts\activate  # Windows
    source .venv/bin/activate  # Linux/macOS
    ```

2.  Crie um arquivo `.env` na raiz do projeto contendo sua chave de API do Gemini:
    ```env
    GEMINI_API_KEY="AIzaSySuaChaveDeAqui"
    ```

### Instalação no Modo Desenvolvimento (Local)

Para instalar as dependências e o pacote localmente de forma editável:
```bash
pip install -e .
```

### Instalação Global como Executável CLI

Você pode instalar o projeto diretamente no seu interpretador global para usá-lo em qualquer diretório do terminal:
```bash
pip install .
```
Após a instalação, o comando `anki-generator` estará disponível no seu terminal de forma global.

---

## 3. Estrutura de Diretórios de Dados

O projeto requer duas pastas criadas na raiz para gerenciar arquivos:
*   `content/`: Diretório onde o usuário insere os arquivos `.docx` e `.pdf` que deseja processar.
*   `results/`: Diretório onde o arquivo `.apkg` gerado e os logs de execução são salvos.

---

## 4. Como Executar

### Execução via CLI (Script Local)
```bash
python main.py
```

### Execução via Comando Global (após instalação via pip)
```bash
anki-generator
```

---

## 5. Fluxo Interativo da CLI
Ao iniciar a aplicação, a CLI guiará você nos seguintes passos:
1.  **Seleção de Fontes:** Lista de arquivos encontrados no diretório `content/` e prompt para inserção de links do YouTube.
2.  **Pré-análise:** O Gemini sugere tópicos/temas identificados no material de estudo e recomenda uma quantidade ideal de cartões.
3.  **Quantidade de Cartões:** Solicita a quantidade de cartões que você deseja gerar (com o default sugerido pela pré-análise).
4.  **Idioma:** Escolha do idioma de geração dos flashcards (Português, Inglês ou Espanhol).
5.  **Modalidade:** Escolha entre "Apenas Texto" ou "Texto + Áudio (TTS)".
6.  **Forma de Exportação:** Opção entre gerar o pacote portátil `genanki (.apkg)` ou injetar diretamente no Anki Desktop via `AnkiConnect`.
