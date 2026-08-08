"""Docling-backed chunker.

Docling and transformers are heavy optional dependencies (they pull in the
whole model stack). They are imported inside ``__init__`` rather than at module
level so that importing this module -- which happens through package imports
and during test collection -- does not require the ``ingestion`` extra to be
installed. Anyone who actually constructs a ``DoclingChunker`` needs them, and
gets a clear message if they are missing.
"""

import logging
from typing import Any

from src.core.interfaces.chunker import IChunker, RawChunk

logger = logging.getLogger(__name__)


class DoclingChunker(IChunker):
    """Implementation of IChunker using Docling HybridChunker."""

    def __init__(
        self,
        max_tokens: int = 512,
        model_id: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        """
        Initialize the Docling chunker.

        Args:
            max_tokens: Maximum tokens per chunk.
            model_id: Tokenizer model ID.
        """
        try:
            from docling.chunking import HybridChunker
            from transformers import AutoTokenizer
        except ImportError as exc:  # pragma: no cover - depends on the extra
            raise ImportError(
                "DoclingChunker requires the optional 'ingestion' extra. "
                "Install it with: pip install -e '.[ingestion]'"
            ) from exc

        self.max_tokens = max_tokens
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.chunker = HybridChunker(
            tokenizer=self.tokenizer, max_tokens=max_tokens, merge_peers=True
        )
        logger.info(f"DoclingChunker initialized (max_tokens={max_tokens})")

    async def chunk_document(
        self, content: str, title: str, source: str, docling_doc: Any | None = None
    ) -> list[RawChunk]:
        """Chunk a document using Docling's HybridChunker."""
        if not content.strip():
            return []

        base_metadata = {
            "title": title,
            "source": source,
            "chunk_method": "hybrid",
        }

        if docling_doc is None:
            logger.warning(
                "No DoclingDocument provided, returning single chunk as fallback"
            )
            return [
                RawChunk(
                    content=content,
                    index=0,
                    metadata={**base_metadata, "chunk_method": "fallback_single"},
                    token_count=len(self.tokenizer.encode(content)),
                )
            ]

        try:
            chunk_iter = self.chunker.chunk(dl_doc=docling_doc)
            chunks = list(chunk_iter)

            raw_chunks = []
            for i, chunk in enumerate(chunks):
                contextualized_text = self.chunker.contextualize(chunk=chunk)
                token_count = len(self.tokenizer.encode(contextualized_text))

                raw_chunks.append(
                    RawChunk(
                        content=contextualized_text.strip(),
                        index=i,
                        metadata={
                            **base_metadata,
                            "total_chunks": len(chunks),
                            "has_context": True,
                        },
                        token_count=token_count,
                    )
                )

            logger.info(f"Created {len(raw_chunks)} chunks using Docling HybridChunker")
            return raw_chunks

        except Exception as e:
            logger.error(f"HybridChunker failed: {e}")
            return [
                RawChunk(
                    content=content,
                    index=0,
                    metadata={**base_metadata, "chunk_method": "error_fallback"},
                    token_count=len(self.tokenizer.encode(content)),
                )
            ]
