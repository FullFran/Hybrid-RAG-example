import logging
import os
from typing import Dict, Any

from src.core.interfaces.embedder import IEmbedder
from src.core.interfaces.repository import IRepository
from src.core.interfaces.parser import IParser
from src.core.interfaces.chunker import IChunker
from src.core.schemas.chunk import Chunk
from src.core.schemas.document import Document

logger = logging.getLogger(__name__)


class IngestService:
    """Business logic for document ingestion."""

    def __init__(
        self,
        repository: IRepository,
        embedder: IEmbedder,
        parser: IParser,
        chunker: IChunker,
    ):
        """
        Initialize IngestService.

        Args:
            repository: Repository for storing documents and chunks.
            embedder: Embedder for generating vector representations.
            parser: Parser for extracting content from files.
            chunker: Chunker for splitting content into fragments.
        """
        self.repository = repository
        self.embedder = embedder
        self.parser = parser
        self.chunker = chunker

    async def ingest_file(self, file_path: str, metadata: Dict[str, Any] = None):
        """
        Process and save a single file.

        Orchestrates the full pipeline: Parse -> Chunk -> Embed -> Save.
        """
        # 1. Parse
        content, raw_doc = await self.parser.parse(file_path)
        title = self._extract_title(content, file_path)

        # 2. Create Document
        document = Document(
            title=title,
            source=os.path.basename(file_path),
            content=content,
            metadata={"file_path": file_path, **(metadata or {})},
        )
        doc_id = await self.repository.save_document(document)

        # 3. Chunk
        raw_chunks = await self.chunker.chunk_document(
            content=content,
            title=title,
            source=document.source,
            docling_doc=raw_doc,
        )

        if not raw_chunks:
            logger.warning(f"No chunks created for document: {title}")
            return doc_id

        # 4. Embed & Map to Domain Chunk
        texts = [rc.content for rc in raw_chunks]
        embeddings = await self.embedder.get_embeddings(texts)

        domain_chunks = []
        for i, (rc, emb) in enumerate(zip(raw_chunks, embeddings)):
            domain_chunks.append(
                Chunk(
                    document_id=doc_id,
                    content=rc.content,
                    embedding=emb,
                    chunk_index=rc.index,
                    metadata=rc.metadata,
                    token_count=rc.token_count,
                )
            )

        # 5. Save Chunks
        await self.repository.save_chunks(domain_chunks)
        return doc_id

    def _extract_title(self, content: str, file_path: str) -> str:
        """Extract title from document content or filename."""
        lines = content.split("\n")
        for line in lines[:10]:
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
        return os.path.splitext(os.path.basename(file_path))[0]

    async def clean(self):
        """Wipe all documents and chunks from the repository."""
        await self.repository.clean_all()
