# anki_generator - Gerador Automático de Cartões Anki via Inteligência Artificial

O **anki_generator** é um programa em Python que automatiza a criação de cartões de estudo (flashcards) para o aplicativo Anki. Ele lê seus materiais de estudo (resumos no Word, livros em PDF ou vídeo-aulas do YouTube), extrai as informações mais importantes e gera cartões contendo perguntas no anverso (frente) e respostas acompanhadas de áudio (voz) no verso.

---

## 1. O que é o Anki e como este programa ajuda você?

O **Anki** é um aplicativo de memorização baseado em cartões de estudo (frente e verso) com repetição espaçada. Criar esses cartões manualmente pode consumir muito tempo. 
Este programa resolve isso: ele funciona como um assistente virtual que:
1.  **Lê seus textos** (Word ou PDF) ou **escuta vídeo-aulas** do YouTube (através da transcrição de legendas).
2.  **Identifica os principais tópicos** e cria perguntas e respostas no idioma que você escolher (Português, Inglês ou Espanhol).
3.  **Gera uma voz de leitura** para a resposta de cada cartão, para que você possa estudar ouvindo a pronúncia correta (ideal para o aprendizado de idiomas).
4.  **Cria um arquivo pronto** (`.apkg`) que você só precisa dar dois cliques para importar diretamente para dentro do seu Anki.

---

## 2. Guia Passo a Passo para Iniciantes (Sem Conhecimento Técnico)

Se você nunca usou programas de terminal em Python, siga este passo a passo simplificado para configurar e rodar o programa no seu computador.

### Passo 1: Instalar o Python
O programa precisa do Python instalado em seu computador para rodar.
*   **Windows:** Baixe e instale a versão mais recente do Python a partir do site oficial: [python.org](https://www.python.org/downloads/). Durante a instalação, **certifique-se de marcar a caixinha "Add Python.exe to PATH"** antes de clicar em instalar.

### Passo 2: Obter sua chave de API do Gemini (Gratuita)
Para que a Inteligência Artificial do Google leia seus materiais e crie as perguntas, você precisa de uma chave de API (uma senha de acesso para desenvolvedores).
1.  Acesse o site do [Google AI Studio](https://aistudio.google.com/).
2.  Faça login com sua conta do Google (Gmail).
3.  Clique no botão **"Get API key"** (Obter chave de API).
4.  Clique em **"Create API key"** e copie o código gerado (uma sequência longa de letras e números). **Guarde este código.**

### Passo 3: Preparar a Pasta do Projeto
1.  Abra a pasta onde você baixou este projeto.
2.  Crie duas novas pastas na raiz (na mesma pasta onde está o arquivo `main.py`):
    *   **`content`**: Coloque aqui os seus arquivos de texto que deseja estudar (seus resumos em `.docx` ou apostilas em `.pdf`).
    *   **`results`**: É aqui que o programa colocará o arquivo de estudos finalizado.
3.  Crie um novo arquivo de texto simples usando o Bloco de Notas, cole sua chave de API nele no seguinte formato, e salve o arquivo com o nome exato de `.env`:
    ```env
    GEMINI_API_KEY="COLE_SUA_CHAVE_AQUI"
    ```

### Passo 4: Rodar o programa pela primeira vez
1.  Abra o terminal do seu computador (no Windows, abra a pasta do projeto, clique na barra de endereços do explorador de arquivos, digite `cmd` e aperte Enter).
2.  Crie um ambiente isolado digitando os seguintes comandos no terminal:
    ```bash
    python -m venv .venv
    .venv\Scripts\activate
    ```
3.  Instale o programa digitando o seguinte comando:
    ```bash
    pip install .
    ```
4.  Coloque seus resumos de estudo dentro da pasta `content` criada anteriormente.
5.  Inicie a criação de cartões rodando o comando:
    ```bash
    anki-generator
    ```

---

## 3. Exemplo Prático de Uso (Na Prática)

Imagine que você quer estudar um resumo sobre "História do Brasil" em Word e uma vídeo-aula de inglês do YouTube.

1.  Você coloca o arquivo `resumo_historia.docx` na pasta `content/`.
2.  Abre o terminal e roda: `anki-generator`.
3.  O programa iniciará um diálogo interativo:
    *   **Pergunta:** *Selecione os arquivos locais para processar:* 
        *   Você marca a caixinha correspondente ao `resumo_historia.docx`.
    *   **Pergunta:** *Insira URLs do YouTube (separadas por vírgula):*
        *   Você digita ou cola a URL do vídeo: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`.
    *   **Etapa Automática:** O programa lê o documento, extrai a legenda do vídeo do YouTube e faz uma análise rápida.
    *   **Sugestão na Tela:** O programa exibe uma tabela identificando que encontrou temas como "Independência do Brasil" e "Gramática de Inglês", sugerindo a criação de 8 cartões de estudo.
    *   **Pergunta:** *Quantos cartões de estudo você deseja gerar?*
        *   Você apenas aperta Enter para aceitar a recomendação de 8 cartões (ou digita outro número de sua preferência).
    *   **Pergunta:** *Selecione o idioma de geração dos cartões:*
        *   Você escolhe `Português` (ou `Inglês` se quiser as perguntas e respostas escritas e faladas em inglês).
    *   **Pergunta:** *Selecione a modalidade dos cartões:*
        *   Você seleciona `Texto + Áudio (TTS)` para gerar a narração de voz.
    *   **Pergunta:** *Selecione a forma de exportação para o Anki:*
        *   Você escolhe `genanki (offline .apkg)`.
4.  **Conclusão:** O programa roda o Gemini, cria os cartões com áudio, limpa os arquivos temporários e exibe uma tabela de resumo.
5.  O seu arquivo de estudos finalizado estará salvo na pasta `results/` com o nome `anki_generator_deck.apkg`.
6.  **Como Estudar:** Abra o seu aplicativo Anki no computador ou celular, vá em **Arquivo > Importar** (ou dê dois cliques no arquivo `.apkg`) e selecione o arquivo. O baralho com as perguntas, respostas e áudios de pronúncia estará pronto para uso.

---

## 4. Guia Técnico (Para Desenvolvedores)

Se você é desenvolvedor e deseja realizar modificações ou rodar os testes automatizados:

### Instalação Editável
```bash
pip install -e .
```

### Estrutura do Módulo de Código
*   `anki_generator/config.py`: Gestão de variáveis e validação do ambiente via `pydantic-settings`.
*   `anki_generator/models.py`: Modelos Pydantic v2 para contratos de dados estruturados.
*   `anki_generator/extractors.py`: Extratores para `.docx`, `.pdf` e YouTube transcripts.
*   `anki_generator/gemini_client.py`: Clientes de API do Gemini para texto e síntese de voz (TTS).
*   `anki_generator/anki_exporter.py`: Módulos de exportação genanki / AnkiConnect.
*   `anki_generator/cli.py`: Orquestrador CLI baseado em `questionary` e `rich`.

### Executando Testes e Qualidade de Código
O projeto exige 100% de conformidade com tipagem estática e formatação.

```bash
# Executa linter de formatação
ruff check .
ruff format --check .

# Executa checagem de tipos estática estrita
mypy anki_generator --strict

# Executa testes unitários e de integração com cobertura de código
pytest --cov=anki_generator --cov-fail-under=80
```

---

## 5. Resolução de Problemas Frequentes

*   **Erro: `ValidationError` / Chave de API não configurada:**
    Certifique-se de que criou o arquivo `.env` exatamente com esse nome (sem extensão `.txt` no final) e inseriu a variável `GEMINI_API_KEY` corretamente nele.
*   **Vídeo do YouTube falha na extração de texto:**
    A extração do YouTube consome as legendas do vídeo. Se o vídeo não tiver legendas geradas automaticamente ou criadas pelo autor, a extração falhará. O programa avisará você e permitirá continuar usando apenas os arquivos da pasta `content/`.
*   **O som do cartão não toca no Anki:**
    Certifique-se de que os alto-falantes estão ligados. Os áudios são importados no formato de mídia nativa do Anki. Se estiver usando o modo AnkiConnect, certifique-se de que o aplicativo Anki Desktop estava aberto no momento em que você gerou os cartões.
