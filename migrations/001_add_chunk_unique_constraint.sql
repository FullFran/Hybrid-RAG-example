-- Migration: Add unique constraint for chunk upsert
-- Issue #13: Prevent duplicate chunks on re-ingestion
-- Run this in Supabase SQL Editor

-- Step 1: Remove any existing duplicates (keep the most recent)
DELETE FROM chunks a
USING chunks b
WHERE a.id < b.id
  AND a.document_id = b.document_id
  AND a.chunk_index = b.chunk_index;

-- Step 2: Add unique constraint
ALTER TABLE chunks
ADD CONSTRAINT chunks_document_id_chunk_index_unique 
UNIQUE (document_id, chunk_index);

-- Verify constraint was created
SELECT 
    conname AS constraint_name,
    contype AS constraint_type
FROM pg_constraint
WHERE conrelid = 'chunks'::regclass
  AND conname LIKE '%unique%';
