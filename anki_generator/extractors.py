import os
import re
import structlog
from typing import TypedDict
from docx import Document  # type: ignore[import-untyped]
from pypdf import PdfReader
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
)

logger = structlog.get_logger()


class TranscriptEntry(TypedDict):
    text: str
    start: float
    duration: float


class ExtractorError(Exception):
    """Exceção base para erros nos extratores."""

    pass


class TranscriptUnavailableError(ExtractorError):
    """Exceção levantada quando a transcrição do YouTube não está disponível."""

    pass


def validate_safe_path(base_dir: str, target_path: str) -> str:
    """Valida se o caminho de destino reside dentro do diretório base (evita path traversal)."""
    abs_base = os.path.abspath(base_dir)
    abs_target = os.path.abspath(target_path)
    if not abs_target.startswith(abs_base):
        raise ValueError(
            "Acesso negado: o caminho do arquivo está fora do diretório permitido."
        )
    return abs_target


def extract_docx(file_path: str) -> str:
    """Extrai o texto contido em um arquivo Word (.docx)."""
    logger.info("Iniciando extração de arquivo Word", file_path=file_path)
    try:
        doc = Document(file_path)
        paragraphs_text = [p.text for p in doc.paragraphs]
        return "\n".join(paragraphs_text)
    except Exception as e:
        logger.error(
            "Erro na extração de arquivo Word", error=str(e), file_path=file_path
        )
        raise ExtractorError(f"Falha ao extrair texto do arquivo Word: {e}") from e


def extract_pdf(file_path: str) -> str:
    """Extrai o texto contido em um arquivo PDF (.pdf) localmente."""
    logger.info("Iniciando extração de PDF", file_path=file_path)
    try:
        reader = PdfReader(file_path)
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return "\n".join(text_parts)
    except Exception as e:
        logger.error("Erro na extração de PDF", error=str(e), file_path=file_path)
        raise ExtractorError(f"Falha ao extrair texto do arquivo PDF: {e}") from e


def extract_youtube_video_id(url: str) -> str:
    """Extrai o ID de 11 caracteres de uma URL do YouTube."""
    patterns = [
        r"(?:v=|\/v\/|embed\/|shorts\/|youtu\.be\/|\/embed\/|\/watch\?v=|\&v=)([^#\&\?]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    # Fallback caso seja passado diretamente o ID de 11 caracteres
    if len(url) == 11 and re.match(r"^[a-zA-Z0-9_-]{11}$", url):
        return url
    raise ValueError(f"Não foi possível extrair o ID do vídeo do YouTube da URL: {url}")


def extract_youtube_transcript(url: str) -> list[TranscriptEntry]:
    """Obtém a transcrição de um vídeo do YouTube com seus respectivos timestamps."""
    logger.info("Obtendo transcrição do YouTube", url=url)
    video_id = extract_youtube_video_id(url)
    try:
        # Instancia a API e lista as transcrições disponíveis
        transcript_list = YouTubeTranscriptApi().list(video_id)
        # Seleciona a primeira transcrição disponível (idioma padrão/original)
        first_transcript = next(iter(transcript_list))
        transcript = first_transcript.fetch()
        return [
            TranscriptEntry(
                text=entry.text,
                start=float(entry.start),
                duration=float(entry.duration),
            )
            for entry in transcript
        ]
    except (TranscriptsDisabled, NoTranscriptFound) as e:
        logger.error("Transcrições indisponíveis no vídeo", error=str(e), url=url)
        raise TranscriptUnavailableError(
            f"Transcrições desativadas ou indisponíveis para o vídeo: {url}"
        ) from e
    except Exception as e:
        logger.error(
            "Erro genérico ao obter transcrição do YouTube", error=str(e), url=url
        )
        raise TranscriptUnavailableError(
            f"Erro ao obter transcrição do YouTube: {e}"
        ) from e


def scan_content_directory(directory_path: str) -> list[str]:
    """Escaneia a pasta content por arquivos suportados (.docx e .pdf)."""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path, exist_ok=True)

    files = []
    for file_name in os.listdir(directory_path):
        if file_name.endswith((".docx", ".pdf")) and file_name != ".gitkeep":
            raw_path = os.path.join(directory_path, file_name)
            try:
                safe_path = validate_safe_path(directory_path, raw_path)
                files.append(safe_path)
            except ValueError as e:
                logger.warning(
                    "Caminho inseguro detectado e ignorado", error=str(e), path=raw_path
                )
    return files
