-- Migration: Initial Core Schema and Semantic Search RPC
-- Part of Review Issue #10: Explicit semantic_score

-- 1. Documents Table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    source TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 2. Chunks Table
CREATE TABLE IF NOT EXISTS chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    embedding vector(1536), -- Adjust dimensions for your model
    metadata JSONB DEFAULT '{}'::jsonb
);

-- 3. Match Chunks RPC (Semantic Search)
-- Renames 'similarity' column to 'semantic_score' for clarity
CREATE OR REPLACE FUNCTION match_chunks (
  query_embedding vector(1536),
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  id uuid,
  document_id uuid,
  content text,
  chunk_index int,
  metadata jsonb,
  semantic_score float, -- Renamed from similarity (Review Point #10)
  doc_title text,
  doc_source text
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
    1 - (c.embedding <=> query_embedding) AS semantic_score,
    d.title AS doc_title,
    d.source AS doc_source
  FROM chunks c
  JOIN documents d ON c.document_id = d.id
  WHERE 1 - (c.embedding <=> query_embedding) > match_threshold
  ORDER BY semantic_score DESC
  LIMIT match_count;
END;
$$;
