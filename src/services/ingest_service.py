import logging
import os
from typing import Any

from src.core.interfaces.embedder import IEmbedder
from src.core.interfaces.repository import IRepository
from src.core.schemas.chunk import Chunk
from src.core.schemas.document import Document
from src.ingestion.chunker import DoclingHybridChunker

logger = logging.getLogger(__name__)


class IngestService:
    """Business logic for document ingestion."""

    def __init__(
        self,
        repository: IRepository,
        embedder: IEmbedder,
        chunker: DoclingHybridChunker,
    ):
        self.repository = repository
        self.embedder = embedder
        self.chunker = chunker

    async def ingest_file(
        self, file_path: str, content: str, title: str, docling_doc: Any = None
    ):
        """Process and save a single file."""
        # 1. Create Document
        document = Document(
            title=title,
            source=os.path.basename(file_path),
            content=content,
            metadata={"file_path": file_path},
        )
        doc_id = await self.repository.save_document(document)

        # 2. Chunk
        raw_chunks = await self.chunker.chunk_document(
            content=content,
            title=title,
            source=document.source,
            docling_doc=docling_doc,
        )

        # 3. Embed & Map to Domain Chunk
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

        # 4. Save Chunks
        await self.repository.save_chunks(domain_chunks)
        return doc_id

    async def clean(self):
        """Wipe all documents and chunks from the repository."""
        await self.repository.clean_all()
