# anki_generator - Automatic Anki Flashcard Generator via Artificial Intelligence

**anki_generator** is a Python command-line utility that automates the creation of study flashcards for the Anki application. It reads your study materials (Word summaries, PDF textbooks, or YouTube lectures), extracts the most critical information, and generates flashcards containing questions on the front and answers accompanied by high-quality speech audio on the back.

---

## 1. What is Anki and how does this tool help you?

**Anki** is a popular spaced-repetition flashcard application. Manually creating cards is a tedious and time-consuming task. 
This program acts as a virtual study assistant that:
1.  **Reads your texts** (Word or PDF files) or **listens to YouTube lectures** (via subtitle transcript extraction).
2.  **Identifies key topics** and generates clean questions and answers in your chosen language (Portuguese, English, or Spanish) using a low model temperature of 0.1 to guarantee highly deterministic and consistent AI outputs.
3.  **Generates spoken audio** for the answer of each card, so you can study by listening to correct pronunciation (ideal for language acquisition).
4.  **Enables typed answers (Type-in-the-Answer)**: The flashcards are pre-configured to let you type your response directly into Anki. When you reveal the card, it displays a side-by-side color comparison (green for matches, red for spelling discrepancies or omissions).
5.  **Creates custom-named decks**: You specify the deck name directly inside the terminal CLI, and the program will build the `.apkg` package with that exact name.
6.  **Produces ready-to-import files**: Generates a file you can double-click to import into Anki, or pushes notes directly into your collection using AnkiConnect.

---

## 2. Step-by-Step Guide for Beginners (No Technical Background)

If you have never worked with command-line tools or Python before, follow these simplified steps to set up and run the generator on your system.

### Step 1: Install Python
The program requires Python to be installed on your computer.
*   **Windows:** Download and install the latest stable version of Python from [python.org](https://www.python.org/downloads/). During the installation wizard, **make sure to check the box that says "Add Python.exe to PATH"** before clicking Install.

### Step 2: Obtain your Google Gemini API Key (Free)
To allow Google's AI to scan your materials and construct questions, you need an API key.
1.  Visit [Google AI Studio](https://aistudio.google.com/).
2.  Log in using your standard Google/Gmail account.
3.  Click the **"Get API key"** button.
4.  Click **"Create API key"** and copy the long string of letters and numbers. **Keep this code secure.**

### Step 3: Prepare the Project Directory
1.  Open the folder where you downloaded this project.
2.  Create two new folders in the root directory (the same folder where `main.py` is located):
    *   **`content`**: Place the documents you want to study here (e.g., `.docx` summaries, lecture notes, or `.pdf` files).
    *   **`results`**: This is where the final study package will be exported.
3.  Create a new text file using Notepad, paste your API key inside it in the format shown below, and save the file with the exact name `.env`:
    ```env
    # Google Gemini API Key (required)
    GEMINI_API_KEY="PASTE_YOUR_API_KEY_HERE"

    # Optional settings
    ANKI_CONNECT_URL="http://localhost:8765"
    LOG_LEVEL="INFO"
    ```

### Step 4: Run the Program for the First Time
1.  Open your command prompt/terminal (on Windows, open the project folder in File Explorer, click the address bar, type `cmd`, and press Enter).
2.  Set up an isolated virtual environment and activate it by running:
    ```bash
    python -m venv .venv
    .venv\Scripts\activate
    ```
3.  Install the package by typing:
    ```bash
    pip install .
    ```
4.  Ensure your study documents are inside the `content` directory.
5.  Execute the generator:
    ```bash
    anki-generator
    ```
    *(If your system blocks the execution of the `.exe` wrapper, you can run it via Python instead):*
    ```bash
    python -m anki_generator
    # or
    python main.py
    ```

---

## 3. Practical Usage Example (In Action)

Let's say you want to study a Word document about "Brazilian History" and a YouTube English grammar lesson.

1.  Place the `brazilian_history.docx` file inside the `content/` folder.
2.  Open your terminal and run: `anki-generator`.
3.  The CLI will launch an interactive wizard:
    *   **Prompt:** *Selecione os arquivos locais para processar (Select local files to process):* 
        *   Check the box next to `brazilian_history.docx` using spacebar, then press Enter.
    *   **Prompt:** *Insira URLs do YouTube (separadas por vírgula) [Opcional] (Enter YouTube URLs):*
        *   Paste the video link: `https://www.youtube.com/watch?v=dQw4w9WgXcQ` and press Enter.
    *   **Automatic Parsing:** The app extracts text from the document, downloads the YouTube subtitles, and feeds them into a quick content analysis.
    *   **Suggestions Table:** A structured table appears on your screen highlighting topics found (e.g., "Brazilian Independence" and "English Grammar") and suggests generating 8 flashcards.
    *   **Prompt:** *Quantos cartões de estudo você deseja gerar? (How many cards to generate?)*
        *   Press Enter to accept the recommendation of 8 (or type in a different count).
    *   **Prompt:** *Selecione o idioma de geração dos cartões (Select language):*
        *   Select `Português` (or `Inglês`/`Espanhol` if you are generating cards in those languages).
    *   **Prompt:** *Selecione a modalidade dos cartões (Select modality):*
        *   Choose `Texto + Áudio (TTS)` to include spoken audio.
    *   **Prompt:** *Selecione a forma de exportação para o Anki (Select export destination):*
        *   Choose `genanki (offline .apkg)` (to generate a local file) or `AnkiConnect (online via API)` (to sync directly into an active Anki Desktop program).
    *   **Prompt:** *Qual o nome do baralho (deck) do Anki que deseja criar? (Name of the deck):*
        *   Type the name you want, like `Brazilian History` (or accept the default `Estudos`).
4.  **Completion:** The program calls the Gemini API (at temperature `0.1` for maximum accuracy) to compose structured JSON questions/answers and TTS voice files. It then attempts to export. If online export via `AnkiConnect` fails (e.g. if Anki is closed), the program runs a **safety offline fallback** to generate the `.apkg` file, cleans up the local temporary audio files, and prints a final execution table.
5.  Your output package will be available in the `results/` folder under `{DeckName}.apkg` (e.g. `Brazilian History.apkg`).
6.  **How to Study:** 
    *   Open your Anki Desktop or mobile app, select **File > Import** (or double-click the `.apkg` file), and import the package.
    *   When reviewing the cards, Anki will display the question alongside a **text input box**. Type your answer.
    *   Click **Show Answer**. Anki compares your text against the solution, coloring matches in **green** and mismatches in **red**.
    *   The spoken audio pronunciation of the answer plays automatically.
    *   Select the standard memory rating buttons (**Again** / **Hard** / **Good** / **Easy**) to schedule your cards.

---

## 4. Technical Guide (For Developers)

If you are a developer who wants to run tests, modify code, or contribute:

### Editable Installation
```bash
pip install -e .
```

### Module Structure
*   `anki_generator/config.py`: Environment and settings parser leveraging `pydantic-settings`.
*   `anki_generator/models.py`: Pydantic v2 data models for type-safe validation.
*   `anki_generator/extractors.py`: Document extractors for `.docx`, `.pdf`, and YouTube transcript scrubbing.
*   `anki_generator/gemini_client.py`: API wrappers for Google Gemini text and synthesis (TTS) models.
*   `anki_generator/anki_exporter.py`: Export pipeline supporting `genanki` and local `AnkiConnect` API calls.
*   `anki_generator/cli.py`: Interactive command-line terminal controller using `questionary` and `rich`.

### Testing and Quality Assurance
All additions must achieve 100% compliance with static types and styling.

```bash
# Run code syntax and formatting linters
ruff check .
ruff format --check .

# Run strict type checking
mypy anki_generator --strict

# Run tests and evaluate coverage limits
pytest --cov=anki_generator --cov-fail-under=80
```

---

## 5. Troubleshooting

*   **Error: `ValidationError` / API key not set:**
    Verify your `.env` file is named exactly `.env` (no trailing `.txt` extensions) and contains the correct `GEMINI_API_KEY` configuration line.
*   **YouTube extraction failure:**
    YouTube scraping relies on subtitle tracks. If a video has no caption tracks (auto-generated or manually uploaded by the author), extraction fails. The app will warn you and allow you to proceed using your local `content/` folder files.
*   **AnkiConnect Error / Offline Fallback:**
    If you chose direct export via `AnkiConnect` but your Anki Desktop is closed or lacks the AnkiConnect add-on listening on port `8765`, the console prints a warning and falls back to saving a `.apkg` file in your `results/` directory automatically.
*   **Audio does not play in Anki:**
    Check your sound output settings. Audio is synthesized by the `gemini-3.1-flash-tts-preview` model, saved as a WAV file, and packaged inside Anki. If using AnkiConnect, make sure Anki Desktop was running during generation so it could register media assets.
*   **App Control Policy blocks `anki-generator.exe` on Windows:**
    If Windows Defender Application Control (WDAC) or AppLocker blocks the wrapper executable, bypass it by running the application using the Python interpreter directly:
    ```bash
    python -m anki_generator
    # or
    python main.py
    ```
