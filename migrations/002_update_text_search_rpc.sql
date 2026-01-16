-- Migration: Update text_search_chunks RPC to return chunk_index
-- Issue #15: Fix lost chunk_index in text search
-- Run this in Supabase SQL Editor

-- Drop ALL existing versions of the function
DROP FUNCTION IF EXISTS text_search_chunks(TEXT, INTEGER);
DROP FUNCTION IF EXISTS text_search_chunks(TEXT);
DROP FUNCTION IF EXISTS public.text_search_chunks;

-- Create updated function with chunk_index
CREATE OR REPLACE FUNCTION text_search_chunks(
    query_text TEXT,
    match_count INTEGER DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    document_id UUID,
    content TEXT,
    chunk_index INTEGER,
    metadata JSONB,
    text_score REAL, -- Renamed for consistency (Review Point #15)
    doc_title TEXT,
    doc_source TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id,
        c.document_id,
        c.content,
        c.chunk_index,
        c.metadata,
        ts_rank(
            to_tsvector('spanish', c.content),
            plainto_tsquery('spanish', query_text)
        )::REAL AS text_score,
        d.title AS doc_title,
        d.source AS doc_source
    FROM chunks c
    JOIN documents d ON c.document_id = d.id
    WHERE to_tsvector('spanish', c.content) @@ plainto_tsquery('spanish', query_text)
    ORDER BY text_score DESC
    LIMIT match_count;
END;
$$;

-- Grant access to authenticated users
GRANT EXECUTE ON FUNCTION text_search_chunks TO authenticated;
GRANT EXECUTE ON FUNCTION text_search_chunks TO anon;

-- Test the function
-- SELECT * FROM text_search_chunks('test query', 5);
