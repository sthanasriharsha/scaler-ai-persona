import os
import time
from pinecone import Pinecone
from google import genai

_pinecone_index = None
_genai_client = None

def get_client():
    global _genai_client
    if _genai_client is None:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        _genai_client = genai.Client(api_key=api_key)
    return _genai_client

def get_index():
    global _pinecone_index
    if _pinecone_index is None:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        _pinecone_index = pc.Index(os.getenv("PINECONE_INDEX", "sriharsha-persona"))
    return _pinecone_index

def embed(text: str) -> list:
    client = get_client()
    r = client.models.embed_content(
        model="models/gemini-embedding-001",
        contents=text,
    )
    return r.embeddings[0].values

def retrieve(query: str, top_k: int = 5) -> list:
    vector = embed(query)
    index = get_index()
    results = index.query(vector=vector, top_k=top_k, include_metadata=True)
    return [
        {"score": m.score, "text": m.metadata.get("text", ""),
         "source": m.metadata.get("source", "")}
        for m in results.matches
    ]

def build_context(chunks: list) -> str:
    return "\n\n---\n\n".join(
        f"[Source: {c['source']}]\n{c['text']}" for c in chunks
    )
