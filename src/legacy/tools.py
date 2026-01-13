"""Search tools for MongoDB RAG Agent."""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from pydantic_ai import RunContext
from pydantic import BaseModel, Field
from pymongo.errors import OperationFailure

from src.dependencies import AgentDependencies

logger = logging.getLogger(__name__)


class SearchResult(BaseModel):
    """Model for search results."""

    chunk_id: str = Field(..., description="MongoDB ObjectId of chunk as string")
    document_id: str = Field(..., description="Parent document ObjectId as string")
    content: str = Field(..., description="Chunk text content")
    similarity: float = Field(..., description="Relevance score (0-1)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")
    document_title: str = Field(..., description="Title from document lookup")
    document_source: str = Field(..., description="Source from document lookup")


async def semantic_search(
    ctx: RunContext[AgentDependencies],
    query: str,
    match_count: Optional[int] = None
) -> List[SearchResult]:
    """
    Perform pure semantic search using MongoDB vector similarity.

    Args:
        ctx: Agent runtime context with dependencies
        query: Search query text
        match_count: Number of results to return (default: 10)

    Returns:
        List of search results ordered by similarity

    Raises:
        OperationFailure: If MongoDB operation fails (e.g., missing index)
    """
    try:
        deps = ctx.deps

        # Use default if not specified
        if match_count is None:
            match_count = deps.settings.default_match_count

        # Validate match count
        match_count = min(match_count, deps.settings.max_match_count)

        # Generate embedding for query (already returns list[float])
        query_embedding = await deps.get_embedding(query)

        # Build MongoDB aggregation pipeline
        pipeline = [
            {
                "$vectorSearch": {
                    "index": deps.settings.mongodb_vector_index,
                    "queryVector": query_embedding,
                    "path": "embedding",
                    "numCandidates": 100,  # Search space (10x limit is good default)
                    "limit": match_count
                }
            },
            {
                "$lookup": {
                    "from": deps.settings.mongodb_collection_documents,
                    "localField": "document_id",
                    "foreignField": "_id",
                    "as": "document_info"
                }
            },
            {
                "$unwind": "$document_info"
            },
            {
                "$project": {
                    "chunk_id": "$_id",
                    "document_id": 1,
                    "content": 1,
                    "similarity": {"$meta": "vectorSearchScore"},
                    "metadata": 1,
                    "document_title": "$document_info.title",
                    "document_source": "$document_info.source"
                }
            }
        ]

        # Execute aggregation
        collection = deps.db[deps.settings.mongodb_collection_chunks]
        cursor = await collection.aggregate(pipeline)
        results = [doc async for doc in cursor][:match_count]

        # Convert to SearchResult objects (ObjectId → str conversion)
        search_results = [
            SearchResult(
                chunk_id=str(doc['chunk_id']),
                document_id=str(doc['document_id']),
                content=doc['content'],
                similarity=doc['similarity'],
                metadata=doc.get('metadata', {}),
                document_title=doc['document_title'],
                document_source=doc['document_source']
            )
            for doc in results
        ]

        logger.info(
            f"semantic_search_completed: query={query}, results={len(search_results)}, match_count={match_count}"
        )

        return search_results

    except OperationFailure as e:
        error_code = e.code if hasattr(e, 'code') else None
        logger.error(
            f"semantic_search_failed: query={query}, error={str(e)}, code={error_code}"
        )
        # Return empty list on error (graceful degradation)
        return []
    except Exception as e:
        logger.exception(f"semantic_search_error: query={query}, error={str(e)}")
        return []


async def text_search(
    ctx: RunContext[AgentDependencies],
    query: str,
    match_count: Optional[int] = None
) -> List[SearchResult]:
    """
    Perform full-text search using MongoDB Atlas Search.

    Uses $search operator for keyword matching, fuzzy matching, and phrase matching.
    Works on all Atlas tiers including M0 (free tier).

    Args:
        ctx: Agent runtime context with dependencies
        query: Search query text
        match_count: Number of results to return (default: 10)

    Returns:
        List of search results ordered by text relevance

    Raises:
        OperationFailure: If MongoDB operation fails (e.g., missing index)
    """
    try:
        deps = ctx.deps

        # Use default if not specified
        if match_count is None:
            match_count = deps.settings.default_match_count

        # Validate match count
        match_count = min(match_count, deps.settings.max_match_count)

        # Build MongoDB Atlas Search aggregation pipeline
        pipeline = [
            {
                "$search": {
                    "index": deps.settings.mongodb_text_index,
                    "text": {
                        "query": query,
                        "path": "content",
                        "fuzzy": {
                            "maxEdits": 2,
                            "prefixLength": 3
                        }
                    }
                }
            },
            {
                "$limit": match_count * 2  # Over-fetch for better RRF results
            },
            {
                "$lookup": {
                    "from": deps.settings.mongodb_collection_documents,
                    "localField": "document_id",
                    "foreignField": "_id",
                    "as": "document_info"
                }
            },
            {
                "$unwind": "$document_info"
            },
            {
                "$project": {
                    "chunk_id": "$_id",
                    "document_id": 1,
                    "content": 1,
                    "similarity": {"$meta": "searchScore"},  # Text relevance score
                    "metadata": 1,
                    "document_title": "$document_info.title",
                    "document_source": "$document_info.source"
                }
            }
        ]

        # Execute aggregation
        collection = deps.db[deps.settings.mongodb_collection_chunks]
        cursor = await collection.aggregate(pipeline)
        results = [doc async for doc in cursor][:match_count * 2]

        # Convert to SearchResult objects (ObjectId → str conversion)
        search_results = [
            SearchResult(
                chunk_id=str(doc['chunk_id']),
                document_id=str(doc['document_id']),
                content=doc['content'],
                similarity=doc['similarity'],
                metadata=doc.get('metadata', {}),
                document_title=doc['document_title'],
                document_source=doc['document_source']
            )
            for doc in results
        ]

        logger.info(
            f"text_search_completed: query={query}, results={len(search_results)}, match_count={match_count}"
        )

        return search_results

    except OperationFailure as e:
        error_code = e.code if hasattr(e, 'code') else None
        logger.error(
            f"text_search_failed: query={query}, error={str(e)}, code={error_code}"
        )
        # Return empty list on error (graceful degradation)
        return []
    except Exception as e:
        logger.exception(f"text_search_error: query={query}, error={str(e)}")
        return []


def reciprocal_rank_fusion(
    search_results_list: List[List[SearchResult]],
    k: int = 60
) -> List[SearchResult]:
    """
    Merge multiple ranked lists using Reciprocal Rank Fusion.

    RRF is a simple yet effective algorithm for combining results from different
    search methods. It works by scoring each document based on its rank position
    in each result list.

    Args:
        search_results_list: List of ranked result lists from different searches
        k: RRF constant (default: 60, standard in literature)

    Returns:
        Unified list of results sorted by combined RRF score

    Algorithm:
        For each document d appearing in result lists:
            RRF_score(d) = Σ(1 / (k + rank_i(d)))
        Where rank_i(d) is the position of document d in result list i.

    References:
        - Cormack et al. (2009): "Reciprocal Rank Fusion outperforms the best system"
        - Standard k=60 performs well across various datasets
    """
    # Build score dictionary by chunk_id
    rrf_scores: Dict[str, float] = {}
    chunk_map: Dict[str, SearchResult] = {}

    # Process each search result list
    for results in search_results_list:
        for rank, result in enumerate(results):
            chunk_id = result.chunk_id

            # Calculate RRF contribution: 1 / (k + rank)
            rrf_score = 1.0 / (k + rank)

            # Accumulate score (automatic deduplication)
            if chunk_id in rrf_scores:
                rrf_scores[chunk_id] += rrf_score
            else:
                rrf_scores[chunk_id] = rrf_score
                chunk_map[chunk_id] = result

    # Sort by combined RRF score (descending)
    sorted_chunks = sorted(
        rrf_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    # Build final result list with updated similarity scores
    merged_results = []
    for chunk_id, rrf_score in sorted_chunks:
        result = chunk_map[chunk_id]
        # Create new result with updated similarity (RRF score)
        merged_result = SearchResult(
            chunk_id=result.chunk_id,
            document_id=result.document_id,
            content=result.content,
            similarity=rrf_score,  # Combined RRF score
            metadata=result.metadata,
            document_title=result.document_title,
            document_source=result.document_source
        )
        merged_results.append(merged_result)

    logger.info(f"RRF merged {len(search_results_list)} result lists into {len(merged_results)} unique results")

    return merged_results


async def hybrid_search(
    ctx: RunContext[AgentDependencies],
    query: str,
    match_count: Optional[int] = None,
    text_weight: Optional[float] = None
) -> List[SearchResult]:
    """
    Perform hybrid search combining semantic and keyword matching.

    Uses manual Reciprocal Rank Fusion (RRF) to merge vector and text search results.
    Works on all Atlas tiers including M0 (free tier) - no M10+ required!

    Args:
        ctx: Agent runtime context with dependencies
        query: Search query text
        match_count: Number of results to return (default: 10)
        text_weight: Weight for text matching (0-1, not used with RRF)

    Returns:
        List of search results sorted by combined RRF score

    Algorithm:
        1. Run semantic search (vector similarity)
        2. Run text search (keyword/fuzzy matching)
        3. Merge results using Reciprocal Rank Fusion
        4. Return top N results by combined score
    """
    try:
        deps = ctx.deps

        # Use defaults if not specified
        if match_count is None:
            match_count = deps.settings.default_match_count

        # Validate match count
        match_count = min(match_count, deps.settings.max_match_count)

        # Over-fetch for better RRF results (2x requested count)
        fetch_count = match_count * 2

        logger.info(f"hybrid_search starting: query='{query}', match_count={match_count}")

        # Run both searches concurrently for performance
        semantic_results, text_results = await asyncio.gather(
            semantic_search(ctx, query, fetch_count),
            text_search(ctx, query, fetch_count),
            return_exceptions=True  # Don't fail if one search errors
        )

        # Handle errors gracefully
        if isinstance(semantic_results, Exception):
            logger.warning(f"Semantic search failed: {semantic_results}, using text results only")
            semantic_results = []
        if isinstance(text_results, Exception):
            logger.warning(f"Text search failed: {text_results}, using semantic results only")
            text_results = []

        # If both failed, return empty
        if not semantic_results and not text_results:
            logger.error("Both semantic and text search failed")
            return []

        # Merge results using Reciprocal Rank Fusion
        merged_results = reciprocal_rank_fusion(
            [semantic_results, text_results],
            k=60  # Standard RRF constant
        )

        # Return top N results
        final_results = merged_results[:match_count]

        logger.info(
            f"hybrid_search_completed: query='{query}', "
            f"semantic={len(semantic_results)}, text={len(text_results)}, "
            f"merged={len(merged_results)}, returned={len(final_results)}"
        )

        return final_results

    except Exception as e:
        logger.exception(f"hybrid_search_error: query={query}, error={str(e)}")
        # Graceful degradation: try semantic-only as last resort
        try:
            logger.info("Falling back to semantic search only")
            return await semantic_search(ctx, query, match_count)
        except:
            return []
