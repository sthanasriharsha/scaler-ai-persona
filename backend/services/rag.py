import os
import google.generativeai as genai
from pinecone import Pinecone

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
_pinecone_index = None

def get_index():
    global _pinecone_index
    if _pinecone_index is None:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        _pinecone_index = pc.Index(os.getenv("PINECONE_INDEX", "sriharsha-persona"))
    return _pinecone_index

def embed(text: str) -> list:
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=text,
        task_type="retrieval_query"
    )
    return result["embedding"]

def retrieve(query: str, top_k: int = 5) -> list:
    vector = embed(query)
    index = get_index()
    results = index.query(vector=vector, top_k=top_k, include_metadata=True)
    return [{"score": m.score, "text": m.metadata.get("text",""), 
             "source": m.metadata.get("source","")} for m in results.matches]

def build_context(chunks: list) -> str:
    return "\n\n---\n\n".join(
        f"[Source: {c['source']}]\n{c['text']}" for c in chunks
    )