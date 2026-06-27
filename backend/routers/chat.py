from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os, json
import google.generativeai as genai
from services.rag import retrieve, build_context
from services.persona import build_prompt

router = APIRouter()

def configure():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    genai.configure(api_key=api_key)

class ChatRequest(BaseModel):
    message: str
    history: list = []

def format_history(history):
    if not history:
        return "No previous messages."
    return "\n".join(
        f"{'User' if h['role']=='user' else 'Sriharsha'}: {h['content']}"
        for h in history[-6:]
    )

@router.post("/chat")
async def chat(req: ChatRequest):
    configure()
    chunks = retrieve(req.message, top_k=5)
    context = build_context(chunks)
    history_str = format_history(req.history)
    messages = build_prompt(context, history_str, req.message)
    full_prompt = messages[0]["content"] + "\n\n" + messages[1]["content"]
    model = genai.GenerativeModel("gemini-2.0-flash")

    def generate():
        try:
            response = model.generate_content(full_prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    yield f"data: {json.dumps({'text': chunk.text})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'text': f'Error: {str(e)}'})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

@router.post("/chat/sync")
async def chat_sync(req: ChatRequest):
    try:
        configure()
        chunks = retrieve(req.message, top_k=5)
        context = build_context(chunks)
        history_str = format_history(req.history)
        messages = build_prompt(context, history_str, req.message)
        full_prompt = messages[0]["content"] + "\n\n" + messages[1]["content"]
        model = genai.GenerativeModel("gemini-2.0-flash")
        resp = model.generate_content(full_prompt)
        return {
            "answer": resp.text,
            "sources": [c["source"] for c in chunks],
            "retrieval_scores": [c["score"] for c in chunks],
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise
