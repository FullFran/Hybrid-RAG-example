import logging
import os
from pathlib import Path
from typing import Any, Optional

from src.core.interfaces.parser import IParser

logger = logging.getLogger(__name__)


class DoclingParser(IParser):
    """Implementation of IParser using Docling."""

    def __init__(self):
        """Initialize the Docling parser."""
        self._initialized = False

    async def parse(self, file_path: str) -> tuple[str, Optional[Any]]:
        """
        Parse a document using Docling.

        Args:
            file_path: Path to the document file.

        Returns:
            Tuple of (markdown_content, docling_document).
        """
        file_ext = os.path.splitext(file_path)[1].lower()

        # Audio formats - transcribe with Whisper ASR
        audio_formats = [".mp3", ".wav", ".m4a", ".flac"]
        if file_ext in audio_formats:
            return await self._transcribe_audio(file_path)

        # Docling-supported formats
        docling_formats = [
            ".pdf",
            ".docx",
            ".doc",
            ".pptx",
            ".ppt",
            ".xlsx",
            ".xls",
            ".html",
            ".htm",
            ".md",
            ".markdown",
        ]

        if file_ext in docling_formats:
            try:
                from docling.document_converter import DocumentConverter

                logger.info(
                    f"Converting {file_ext} file using Docling: {os.path.basename(file_path)}"
                )

                # In a real production scenario, we might want to reuse the converter
                converter = DocumentConverter()
                # Run sync in thread if necessary, but docling is mostly sync anyway
                # For now keeping it simple as in the original code
                result = converter.convert(file_path)

                markdown_content = result.document.export_to_markdown()
                logger.info(
                    f"Successfully converted {os.path.basename(file_path)} to markdown"
                )

                return (markdown_content, result.document)

            except Exception as e:
                logger.error(f"Failed to convert {file_path} with Docling: {e}")
                logger.warning(f"Falling back to raw text extraction for {file_path}")
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        return (f.read(), None)
                except Exception:
                    return (
                        f"[Error: Could not read file {os.path.basename(file_path)}]",
                        None,
                    )

        # Text-based formats
        else:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return (f.read(), None)
            except UnicodeDecodeError:
                with open(file_path, "r", encoding="latin-1") as f:
                    return (f.read(), None)

    async def _transcribe_audio(self, file_path: str) -> tuple[str, Optional[Any]]:
        """Transcribe audio file using Whisper ASR via Docling."""
        try:
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import AsrPipelineOptions
            from docling.datamodel import asr_model_specs
            from docling.document_converter import AudioFormatOption, DocumentConverter
            from docling.pipeline.asr_pipeline import AsrPipeline

            audio_path = Path(file_path).resolve()
            logger.info(
                f"Transcribing audio file using Whisper Turbo: {audio_path.name}"
            )

            if not audio_path.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_path}")

            pipeline_options = AsrPipelineOptions()
            pipeline_options.asr_options = asr_model_specs.WHISPER_TURBO

            converter = DocumentConverter(
                format_options={
                    InputFormat.AUDIO: AudioFormatOption(
                        pipeline_cls=AsrPipeline,
                        pipeline_options=pipeline_options,
                    )
                }
            )

            result = converter.convert(audio_path)
            markdown_content = result.document.export_to_markdown()
            logger.info(f"Successfully transcribed {os.path.basename(file_path)}")

            return (markdown_content, result.document)

        except Exception as e:
            logger.error(f"Failed to transcribe {file_path} with Whisper ASR: {e}")
            return (
                f"[Error: Could not transcribe audio file {os.path.basename(file_path)}]",
                None,
            )
