import logging
from datetime import datetime
from typing import List

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from src.core.interfaces.repository import IRepository
from src.core.schemas.chunk import Chunk
from src.core.schemas.document import Document
from src.core.schemas.search import SearchHit

logger = logging.getLogger(__name__)


class MongoRepository(IRepository):
    """MongoDB implementation of the repository interface."""

    def __init__(
        self, uri: str, db_name: str, doc_collection: str, chunk_collection: str
    ):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[db_name]
        self.documents = self.db[doc_collection]
        self.chunks = self.db[chunk_collection]

    async def save_document(self, document: Document) -> str:
        doc_dict = document.model_dump(exclude={"id"}, by_alias=True, mode="json")
        result = await self.documents.insert_one(doc_dict)
        return str(result.inserted_id)

    async def save_chunks(self, chunks: List[Chunk]) -> None:
        if not chunks:
            return

        chunk_dicts = []
        for chunk in chunks:
            cd = chunk.model_dump(exclude={"id"}, by_alias=True, mode="json")
            # Ensure document_id is ObjectId if it's a string from Mongo
            try:
                cd["document_id"] = ObjectId(cd["document_id"])
            except:
                pass
            chunk_dicts.append(cd)

        await self.chunks.insert_many(chunk_dicts, ordered=False)

    async def semantic_search(
        self, vector: List[float], limit: int, threshold: float | None = None
    ) -> List[SearchHit]:
        index_name = "vector_index"
        pipeline = [
            {
                "$vectorSearch": {
                    "index": index_name,
                    "queryVector": vector,
                    "path": "embedding",
                    "numCandidates": 100,
                    "limit": limit,
                }
            },
            {
                "$lookup": {
                    "from": self.documents.name,
                    "localField": "document_id",
                    "foreignField": "_id",
                    "as": "doc",
                }
            },
            {"$unwind": "$doc"},
            {
                "$project": {
                    "similarity": {"$meta": "vectorSearchScore"},
                    "content": 1,
                    "metadata": 1,
                    "chunk_index": 1,
                    "document_id": 1,
                    "doc_title": "$doc.title",
                    "doc_source": "$doc.source",
                }
            },
        ]

        results = []
        async for doc in self.chunks.aggregate(pipeline):
            chunk = Chunk(
                id=str(doc["_id"]),
                document_id=str(doc["document_id"]),
                content=doc["content"],
                chunk_index=doc["chunk_index"],
                metadata=doc.get("metadata", {}),
                created_at=doc.get("created_at", datetime.now()),
            )
            results.append(
                SearchHit(
                    chunk=chunk,
                    document_title=doc["doc_title"],
                    document_source=doc["doc_source"],
                    semantic_score=doc["similarity"],
                )
            )
        return results

    async def text_search(self, query: str, limit: int) -> List[SearchHit]:
        index_name = "text_index"
        pipeline = [
            {
                "$search": {
                    "index": index_name,
                    "text": {
                        "query": query,
                        "path": "content",
                        "fuzzy": {"maxEdits": 2},
                    },
                }
            },
            {"$limit": limit},
            {
                "$lookup": {
                    "from": self.documents.name,
                    "localField": "document_id",
                    "foreignField": "_id",
                    "as": "doc",
                }
            },
            {"$unwind": "$doc"},
            {
                "$project": {
                    "similarity": {"$meta": "searchScore"},
                    "content": 1,
                    "metadata": 1,
                    "chunk_index": 1,
                    "document_id": 1,
                    "doc_title": "$doc.title",
                    "doc_source": "$doc.source",
                }
            },
        ]

        results = []
        async for doc in self.chunks.aggregate(pipeline):
            chunk = Chunk(
                _id=str(doc["_id"]),
                document_id=str(doc["document_id"]),
                content=doc["content"],
                chunk_index=doc["chunk_index"],
                metadata=doc.get("metadata", {}),
                created_at=doc.get("created_at", datetime.now()),
            )
            results.append(
                SearchHit(
                    chunk=chunk,
                    document_title=doc["doc_title"],
                    document_source=doc["doc_source"],
                    text_score=doc["similarity"],
                )
            )
        return results

    async def close(self):
        self.client.close()
