import os
import httpx
import anthropic
from supabase import create_client
from dotenv import load_dotenv
import numpy as np
import json

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


def cosine_similarity(a: list, b: list) -> float:
    """Calculate cosine similarity between two vectors."""
    a_np = np.array(a)
    b_np = np.array(b)
    return np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np))


async def compress_memories() -> str:
    """
    Compress similar memories by clustering and merging them.
    
    Returns:
        A report of how many memories were compressed
    """
    try:
        # Fetch all memories from Supabase
        result = supabase.table("memories").select("*").execute()
        
        if not result.data or len(result.data) < 2:
            return "Not enough memories to compress (need at least 2)."
        
        memories = result.data
        total_original = len(memories)
        
        # Convert embeddings from strings to numpy arrays
        for mem in memories:
            embedding = mem["embedding"]
            # If embedding is a string, parse it
            if isinstance(embedding, str):
                try:
                    embedding = json.loads(embedding)
                except (json.JSONDecodeError, ValueError):
                    # Try ast.literal_eval as fallback
                    import ast
                    embedding = ast.literal_eval(embedding)
            # Convert to numpy array of floats
            mem["embedding"] = np.array(embedding, dtype=float)
        
        # Group similar memories by finding clusters
        clusters = []
        used_indices = set()
        
        for i, mem1 in enumerate(memories):
            if i in used_indices:
                continue
            
            cluster = [mem1]
            used_indices.add(i)
            
            for j, mem2 in enumerate(memories):
                if j <= i or j in used_indices:
                    continue
                
                # Calculate cosine similarity
                similarity = cosine_similarity(mem1["embedding"], mem2["embedding"])
                
                if similarity > 0.85:
                    cluster.append(mem2)
                    used_indices.add(j)
            
            # Only create clusters with 2+ memories
            if len(cluster) > 1:
                clusters.append(cluster)
        
        if not clusters:
            return "No similar memories found to compress."
        
        # Merge each cluster using Claude
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        compressed_count = 0
        
        for cluster in clusters:
            # Prepare memories for merging
            memory_texts = [mem["content"] for mem in cluster]
            memory_ids = [mem["id"] for mem in cluster]
            
            # Ask Claude to merge them
            merge_prompt = f"""Merge these similar memories into one concise summary that captures all important information:

{chr(10).join(f"{i+1}. {text}" for i, text in enumerate(memory_texts))}

Respond with ONLY the merged memory text, nothing else."""
            
            response = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=500,
                messages=[{"role": "user", "content": merge_prompt}]
            )
            
            merged_content = ""
            for block in response.content:
                if hasattr(block, "text"):
                    merged_content = block.text
                    break
            
            if merged_content:
                # Save the new compressed memory
                await save_memory(merged_content)
                
                # Delete the old individual memories
                for mem_id in memory_ids:
                    supabase.table("memories").delete().eq("id", mem_id).execute()
                
                compressed_count += len(cluster)
        
        total_after = total_original - compressed_count + len(clusters)
        
        return f"""Memory compression complete:
- Original memories: {total_original}
- Memories compressed: {compressed_count}
- New compressed memories: {len(clusters)}
- Total memories after compression: {total_after}
- Space saved: {compressed_count - len(clusters)} memories"""
    
    except Exception as e:
        return f"Error compressing memories: {str(e)}"
