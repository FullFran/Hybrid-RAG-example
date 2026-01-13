import asyncio
import os

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
client = create_client(url, key)


async def check():
    print("Checking database counts...")
    docs = client.table("documents").select("count", count="exact").execute()
    chunks = client.table("chunks").select("count", count="exact").execute()

    print(f"Documents: {docs.count}")
    print(f"Chunks: {chunks.count}")

    if chunks.count > 0:
        print("\nSampling first chunk:")
        sample = client.table("chunks").select("content, embedding").limit(1).execute()
        if sample.data:
            content = sample.data[0].get("content", "")
            emb = sample.data[0].get("embedding")
            print(f"Content: {content[:100]}...")
            print(f"Has Embedding: {emb is not None}")
            if emb:
                # If it's a string, try to parse it
                if isinstance(emb, str):
                    print(f"Embedding is STRING (length: {len(emb)})")
                    import json

                    try:
                        emb_list = json.loads(emb)
                        print(f"Parsed as list of length: {len(emb_list)}")
                    except:
                        print("Failed to parse string as JSON")
                else:
                    print(f"Embedding is {type(emb)} (length: {len(emb)})")

                # Test RPC
                print(
                    "\nTesting Semantic Search RPC with threshold 0.0 (to see anything)..."
                )
                rpc_params = {
                    "query_embedding": emb_list if isinstance(emb, str) else emb,
                    "match_threshold": 0.0,
                    "match_count": 5,
                }
                rpc_res = client.rpc("match_chunks", rpc_params).execute()
                print(f"RPC found {len(rpc_res.data)} matches at 0.0 threshold")
                if rpc_res.data:
                    for i, m in enumerate(rpc_res.data):
                        print(
                            f"  {i + 1}. Sim: {m.get('similarity')} - {m.get('doc_title')}"
                        )


if __name__ == "__main__":
    asyncio.run(check())
