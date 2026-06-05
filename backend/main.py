from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import chat, booking, health
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Sriharsha AI Persona API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")
app.include_router(booking.router, prefix="/api")
app.include_router(health.router, prefix="/api")

@app.get("/")
def root():
    return {"status": "Sriharsha AI Persona API is live"}
