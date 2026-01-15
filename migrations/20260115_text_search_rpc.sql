-- migration: 20260115_text_search_rpc
-- Description: Adds GIN index for full-text search and an RPC function that returns ts_rank.

-- 1. Create GIN index for full-text search on the 'content' column
-- This index speeds up the @@ operator and ts_rank calculations.
CREATE INDEX IF NOT EXISTS chunks_content_search_idx 
ON chunks 
USING gin (to_tsvector('spanish', content));

-- 2. Create RPC for text search with ts_rank
-- This function joins with documents to get metadata in a single call.
-- Returns similarity as ts_rank for better RRF ranking.

-- Necesario para cambiar el tipo de retorno de FLOAT a REAL
DROP FUNCTION IF EXISTS text_search_chunks(INT, TEXT);

CREATE OR REPLACE FUNCTION text_search_chunks(
  match_count INT,
  query_text TEXT
)
RETURNS TABLE (
  id UUID,
  document_id UUID,
  content TEXT,
  metadata JSONB,
  similarity REAL, -- ts_rank returns REAL (single precision)
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
    c.metadata,
    ts_rank(to_tsvector('spanish', c.content), websearch_to_tsquery('spanish', query_text)) AS similarity,
    d.title AS doc_title,
    d.source AS doc_source
  FROM chunks c
  JOIN documents d ON c.document_id = d.id
  WHERE to_tsvector('spanish', c.content) @@ websearch_to_tsquery('spanish', query_text)
  ORDER BY similarity DESC
  LIMIT match_count;
END;
$$;
