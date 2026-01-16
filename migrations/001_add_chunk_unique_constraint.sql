-- Migration: Add unique constraint for chunk upsert
-- Issue #13: Prevent duplicate chunks on re-ingestion
-- Run this in Supabase SQL Editor

-- Step 1: Remove any existing duplicates (keep the most recent)
DELETE FROM chunks a
USING chunks b
WHERE a.id < b.id
  AND a.document_id = b.document_id
  AND a.chunk_index = b.chunk_index;

-- Step 2: Add unique index (Review Point #4)
-- This ensures upsert works correctly
CREATE UNIQUE INDEX IF NOT EXISTS chunks_document_id_chunk_index_idx 
ON chunks (document_id, chunk_index);

-- Step 3: Add explicit embedding version columns (if you go serious)
-- ALTER TABLE chunks ADD COLUMN IF NOT EXISTS embedding_version TEXT DEFAULT 'text-embedding-3-small';

-- Verify index was created
SELECT
    indexname AS index_name,
    indexdef AS index_definition
FROM pg_indexes
WHERE tablename = 'chunks'
  AND indexname LIKE '%unique%';
