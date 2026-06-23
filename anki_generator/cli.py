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
    """Executa a interface de linha de comando (CLI) interativa do anki_generator."""
    console.print(
        Panel(
            "[bold blue]anki_generator - Gerador de Flashcards via Gemini[/bold blue]"
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
            "Selecione os arquivos locais para processar:",
            choices=file_choices,
        ).ask()
        if chosen_names:
            selected_files = [
                f for f in local_files if os.path.basename(f) in chosen_names
            ]

    youtube_urls_input = questionary.text(
        "Insira URLs do YouTube (separadas por vírgula) [Opcional]:"
    ).ask()

    youtube_urls = [url.strip() for url in youtube_urls_input.split(",") if url.strip()]

    if not selected_files and not youtube_urls:
        console.print(
            "[red]Erro: Nenhuma fonte de estudo foi selecionada ou fornecida. Abortando.[/red]"
        )
        return

    console.print("\n[yellow]Extraindo conteúdo das fontes...[/yellow]")
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
                f"[red]Erro ao extrair arquivo {os.path.basename(file_path)}: {e}[/red]"
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
                f"--- Fonte (Vídeo do YouTube: {url}) ---\n{combined_transcript}\n"
            )
        except TranscriptUnavailableError as e:
            console.print(f"[red]Erro ao obter transcrição do vídeo {url}: {e}[/red]")

    combined_text = "\n".join(full_text_parts)
    if not combined_text.strip():
        console.print(
            "[red]Erro: Nenhum texto válido pôde ser extraído das fontes. Abortando.[/red]"
        )
        return

    console.print("[yellow]Realizando pré-análise do conteúdo com o Gemini...[/yellow]")
    client = GeminiClient()
    try:
        suggestion = client.suggest_themes(combined_text)
    except Exception as e:
        console.print(f"[red]Erro na comunicação com a API do Gemini: {e}[/red]")
        return

    console.print("\n[bold green]Análise do material concluída:[/bold green]")
    table = Table(title="Tópicos Identificados")
    table.add_column("Temas", style="cyan")
    table.add_column("Sugestão de Cartões", style="magenta")
    table.add_column("Justificativa", style="green")

    themes_str = ", ".join(suggestion.themes)
    table.add_row(
        themes_str, str(suggestion.suggested_cards_count), suggestion.rationale
    )
    console.print(table)

    count_str = questionary.text(
        "Quantos cartões de estudo você deseja gerar?",
        default=str(suggestion.suggested_cards_count),
        validate=lambda val: val.isdigit() and int(val) > 0,
    ).ask()
    count = int(count_str)

    language = questionary.select(
        "Selecione o idioma de geração dos cartões:",
        choices=["Português", "Inglês", "Espanhol"],
    ).ask()

    modality = questionary.select(
        "Selecione a modalidade dos cartões:",
        choices=["Apenas Texto", "Texto + Áudio (TTS)"],
    ).ask()

    export_mode = questionary.select(
        "Selecione a forma de exportação para o Anki:",
        choices=["genanki (offline .apkg)", "AnkiConnect (online via API)"],
    ).ask()

    console.print("\n[yellow]Gerando cartões de estudo...[/yellow]")
    try:
        collection = client.generate_flashcards(combined_text, count, language)
    except Exception as e:
        console.print(f"[red]Erro ao gerar cartões com o Gemini: {e}[/red]")
        return

    cards_to_process = collection.cards[:count]

    audio_paths: dict[int, str] = {}
    temp_files: list[str] = []

    if modality == "Texto + Áudio (TTS)":
        console.print("[yellow]Gerando arquivos de áudio via TTS...[/yellow]")
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
                    f"[red]Erro ao gerar áudio para o cartão {idx+1}: {e}[/red]"
                )

    console.print("[yellow]Exportando cartões para o Anki...[/yellow]")
    try:
        deck_name = "anki_generator_deck"
        if export_mode == "genanki (offline .apkg)":
            output_apkg = os.path.join("results", f"{deck_name}.apkg")
            export_offline(
                deck_name,
                cards_to_process,
                audio_paths if audio_paths else None,
                output_apkg,
            )
            console.print(
                f"\n[green]Sucesso! Pacote Anki gerado em: {output_apkg}[/green]"
            )
        else:
            export_online(
                deck_name, cards_to_process, audio_paths if audio_paths else None
            )
            console.print(
                "\n[green]Sucesso! Cartões injetados com sucesso via AnkiConnect.[/green]"
            )

        if temp_files:
            console.print("[yellow]Limpando arquivos de áudio temporários...[/yellow]")
            for fp in temp_files:
                if os.path.exists(fp):
                    try:
                        os.remove(fp)
                    except Exception as e:
                        logger.warning(
                            "Falha ao remover arquivo de áudio temporário",
                            path=fp,
                            error=str(e),
                        )

    except Exception as e:
        console.print(f"[red]Erro durante a exportação para o Anki: {e}[/red]")
        return

    console.print("\n[bold green]=== Resumo da Execução ===[/bold green]")
    summary_table = Table()
    summary_table.add_column("Métrica", style="cyan")
    summary_table.add_column("Valor", style="green")
    summary_table.add_row("Cartões solicitados", str(count))
    summary_table.add_row("Cartões efetivamente gerados", str(len(cards_to_process)))
    summary_table.add_row("Idioma", language)
    summary_table.add_row("Modalidade", modality)
    summary_table.add_row("Modo de Exportação", export_mode)
    summary_table.add_row("Fontes locais processadas", str(len(selected_files)))
    summary_table.add_row("Vídeos do YouTube processados", str(len(youtube_urls)))
    console.print(summary_table)
