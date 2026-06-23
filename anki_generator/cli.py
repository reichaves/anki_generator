import os
import questionary
import structlog
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from anki_generator.extractors import (
    scan_content_directory,
    extract_docx,
    extract_pdf,
    extract_youtube_transcript,
    TranscriptUnavailableError,
    ExtractorError,
)
from anki_generator.gemini_client import GeminiClient, save_pcm_as_wav
from anki_generator.anki_exporter import export_offline, export_online

logger = structlog.get_logger()
console = Console()


def run_cli() -> None:
    """Executes the interactive command line interface (CLI) for anki_generator."""
    console.print(
        Panel(
            "[bold blue]anki_generator - Flashcard Generator via Gemini[/bold blue]"
        )
    )

    content_dir = "content"
    if not os.path.exists(content_dir):
        os.makedirs(content_dir, exist_ok=True)

    local_files = scan_content_directory(content_dir)

    selected_files: list[str] = []
    if local_files:
        file_choices = [os.path.basename(f) for f in local_files]
        chosen_names = questionary.checkbox(
            "Select local files to process:",
            choices=file_choices,
        ).ask()
        if chosen_names:
            selected_files = [
                f for f in local_files if os.path.basename(f) in chosen_names
            ]

    youtube_urls_input = questionary.text(
        "Enter YouTube URLs (comma-separated) [Optional]:"
    ).ask()

    youtube_urls = [url.strip() for url in youtube_urls_input.split(",") if url.strip()]

    if not selected_files and not youtube_urls:
        console.print(
            "[red]Error: No study source was selected or provided. Aborting.[/red]"
        )
        return

    console.print("\n[yellow]Extracting content from sources...[/yellow]")
    full_text_parts: list[str] = []

    for file_path in selected_files:
        try:
            if file_path.endswith(".docx"):
                txt = extract_docx(file_path)
                full_text_parts.append(
                    f"--- Fonte (Arquivo Word): {os.path.basename(file_path)} ---\n{txt}\n"
                )
            elif file_path.endswith(".pdf"):
                txt = extract_pdf(file_path)
                full_text_parts.append(
                    f"--- Fonte (Arquivo PDF): {os.path.basename(file_path)} ---\n{txt}\n"
                )
        except ExtractorError as e:
            console.print(
                f"[red]Error extracting file {os.path.basename(file_path)}: {e}[/red]"
            )

    for url in youtube_urls:
        try:
            transcript = extract_youtube_transcript(url)
            transcript_text_parts = []
            for entry in transcript:
                start_sec = int(entry["start"])
                transcript_text_parts.append(f"[{start_sec}s] {entry['text']}")

            combined_transcript = " ".join(transcript_text_parts)
            full_text_parts.append(
                f"--- Source (YouTube Video: {url}) ---\n{combined_transcript}\n"
            )
        except TranscriptUnavailableError as e:
            console.print(f"[red]Error retrieving transcript for video {url}: {e}[/red]")

    combined_text = "\n".join(full_text_parts)
    if not combined_text.strip():
        console.print(
            "[red]Error: No valid text could be extracted from sources. Aborting.[/red]"
        )
        return

    console.print("[yellow]Performing content pre-analysis with Gemini...[/yellow]")
    client = GeminiClient()
    try:
        suggestion = client.suggest_themes(combined_text)
    except Exception as e:
        console.print(f"[red]Error communicating with Gemini API: {e}[/red]")
        return

    console.print("\n[bold green]Material analysis completed:[/bold green]")
    table = Table(title="Identified Topics")
    table.add_column("Themes", style="cyan")
    table.add_column("Suggested Cards", style="magenta")
    table.add_column("Rationale", style="green")

    themes_str = ", ".join(suggestion.themes)
    table.add_row(
        themes_str, str(suggestion.suggested_cards_count), suggestion.rationale
    )
    console.print(table)

    count_str = questionary.text(
        "How many study cards do you want to generate?",
        default=str(suggestion.suggested_cards_count),
        validate=lambda val: val.isdigit() and int(val) > 0,
    ).ask()
    count = int(count_str)

    language = questionary.select(
        "Select the language to generate flashcards in:",
        choices=["Portuguese", "English", "Spanish"],
    ).ask()

    modality = questionary.select(
        "Select the flashcard modality:",
        choices=["Text Only", "Text + Audio (TTS)"],
    ).ask()

    export_mode = questionary.select(
        "Select the export format for Anki:",
        choices=["genanki (offline .apkg)", "AnkiConnect (online via API)"],
    ).ask()

    deck_name = questionary.text(
        "What is the name of the Anki deck you wish to create?",
        default="Estudos",
    ).ask()
    if not deck_name or not deck_name.strip():
        deck_name = "Estudos"

    console.print("\n[yellow]Generating flashcards...[/yellow]")
    try:
        collection = client.generate_flashcards(combined_text, count, language)
    except Exception as e:
        console.print(f"[red]Error generating flashcards with Gemini: {e}[/red]")
        return

    cards_to_process = collection.cards[:count]

    audio_paths: dict[int, str] = {}
    temp_files: list[str] = []

    if modality == "Text + Audio (TTS)":
        console.print("[yellow]Generating audio files via TTS...[/yellow]")
        results_dir = "results"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir, exist_ok=True)

        for idx, card in enumerate(cards_to_process):
            try:
                pcm_data = client.generate_audio(card.answer_text, language)
                filename = f"audio_{idx}_{hash(card.question) % 1000000}.wav"
                filepath = os.path.join(results_dir, filename)
                save_pcm_as_wav(filepath, pcm_data)
                audio_paths[idx] = filepath
                temp_files.append(filepath)
            except Exception as e:
                console.print(
                    f"[red]Error generating audio for card {idx+1}: {e}[/red]"
                )

    console.print("[yellow]Exporting cards to Anki...[/yellow]")
    deck_name = deck_name.strip()
    export_succeeded = False
    output_apkg = os.path.join("results", f"{deck_name}.apkg")

    try:
        if export_mode == "genanki (offline .apkg)":
            export_offline(
                deck_name,
                cards_to_process,
                audio_paths if audio_paths else None,
                output_apkg,
            )
            console.print(
                f"\n[green]Success! Anki package generated at: {output_apkg}[/green]"
            )
            export_succeeded = True
        else:
            try:
                export_online(
                    deck_name, cards_to_process, audio_paths if audio_paths else None
                )
                console.print(
                    "\n[green]Success! Cards successfully injected via AnkiConnect.[/green]"
                )
                export_succeeded = True
            except Exception as online_err:
                console.print(
                    f"\n[yellow]Warning: Online export via AnkiConnect failed ({online_err}).[/yellow]"
                )
                console.print(
                    "[yellow]Initiating safety fallback for offline export...[/yellow]"
                )
                export_offline(
                    deck_name,
                    cards_to_process,
                    audio_paths if audio_paths else None,
                    output_apkg,
                )
                console.print(
                    f"[green]Success! Fallback Anki package generated offline at: {output_apkg}[/green]"
                )
                export_succeeded = True

        if export_succeeded and temp_files:
            console.print("[yellow]Cleaning up temporary audio files...[/yellow]")
            for fp in temp_files:
                if os.path.exists(fp):
                    try:
                        os.remove(fp)
                    except Exception as e:
                        logger.warning(
                            "Failed to remove temporary audio file",
                            path=fp,
                            error=str(e),
                        )

    except Exception as e:
        console.print(f"[red]Critical error during Anki export: {e}[/red]")
        return

    console.print("\n[bold green]=== Execution Summary ===[/bold green]")
    summary_table = Table()
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")
    summary_table.add_row("Requested cards", str(count))
    summary_table.add_row("Cards successfully generated", str(len(cards_to_process)))
    summary_table.add_row("Language", language)
    summary_table.add_row("Modality", modality)
    summary_table.add_row("Export Mode", export_mode)
    summary_table.add_row("Local files processed", str(len(selected_files)))
    summary_table.add_row("YouTube videos processed", str(len(youtube_urls)))
    console.print(summary_table)
