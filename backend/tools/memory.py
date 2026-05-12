import os
import httpx
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

async def get_embedding(text: str) -> list:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": "nomic-embed-text", "prompt": text},
            timeout=30.0
        )
        return response.json()["embedding"]

async def save_memory(content: str) -> str:
    embedding = await get_embedding(content)
    supabase.table("memories").insert({
        "content": content,
        "embedding": embedding
    }).execute()
    return f"Memory saved: {content}"

async def search_memory(query: str) -> str:
    try:
        embedding = await get_embedding(query)
        result = supabase.rpc("match_memories", {
            "query_embedding": embedding,
            "match_threshold": 0.5,
            "match_count": 5
        }).execute()
        if result.data:
            memories = [row["content"] for row in result.data]
            return "\n".join(f"- {m}" for m in memories)
        return "No relevant memories found."
    except Exception as e:
        return f"Memory search error: {e}"