# Sriharsha AI Persona — Scaler Assignment

AI persona of **Gundumalla Sthana Sriharsha** that can be called, chatted with, and used to book an interview — end to end, no human in the loop.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    PART A: Voice Agent                   │
│  Twilio Phone → Vapi Orchestration → ElevenLabs TTS     │
│              ↓ STT (Deepgram) ↓                         │
│         LLM (Claude claude-sonnet-4-20250514) + RAG              │
│              ↓ Cal.com Booking Tool ↓                   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                   PART B: Chat Interface                 │
│  Next.js UI → FastAPI Backend → RAG Pipeline            │
│            → Claude claude-sonnet-4-20250514 (streaming)         │
│            → Cal.com API (booking)                      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              Shared RAG Knowledge Base                   │
│  Resume PDF + GitHub READMEs + Bio Docs                 │
│  → Chunked → OpenAI Embeddings → Pinecone               │
└─────────────────────────────────────────────────────────┘
```

## Cost Breakdown

| Item | Cost |
|------|------|
| Twilio phone number | ~$1.15/month |
| Vapi (voice) | ~$0.05–0.10 per call minute |
| ElevenLabs TTS | ~$0.003 per 1k chars (~free tier) |
| OpenAI embeddings | ~$0.0001 per 1k tokens (one-time ingest) |
| Claude claude-sonnet-4-20250514 (chat) | ~$0.003 per chat session |
| Pinecone | Free tier (100k vectors) |
| Vercel hosting | Free tier |
| **Per call estimate** | **~$0.15–0.25** |
| **Per chat session** | **~$0.003–0.01** |

## Setup Instructions

### 1. Clone & Install

```bash
git clone https://github.com/sthanasriharsha/scaler-ai-persona
cd scaler-ai-persona

# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 2. Environment Variables

Copy `.env.example` to `.env` and fill in:

```bash
# Backend
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key
PINECONE_API_KEY=your_key
PINECONE_INDEX=sriharsha-persona
CALCOM_API_KEY=your_key
CALCOM_EVENT_TYPE_ID=your_event_id
VAPI_API_KEY=your_key

# Frontend
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

### 3. Ingest Knowledge Base

```bash
cd rag
python ingest.py
```

### 4. Deploy Backend

```bash
cd backend
# Railway: connect GitHub repo, set env vars, deploy
# Or locally: uvicorn main:app --reload
```

### 5. Deploy Frontend

```bash
cd frontend
vercel deploy
```

### 6. Set Up Vapi Voice Agent

1. Go to vapi.ai → Create Assistant
2. Paste contents of `vapi/system_prompt.txt` as system prompt
3. Add Cal.com tool from `vapi/calcom_tool.json`
4. Set voice to ElevenLabs → Rachel
5. Connect Twilio phone number
6. Copy phone number for submission

### 7. Run Evals

```bash
cd evals
python run_evals.py
python generate_report.py  # outputs evals_report.pdf
```

## Submission Checklist

- [ ] Voice agent phone number (from Vapi)
- [ ] Public chat URL (from Vercel)
- [ ] This GitHub repo (public)
- [ ] `evals/evals_report.pdf`
- [ ] Loom walkthrough ≤ 4 min
