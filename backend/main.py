"""
main.py — ShipStack AI Tool Agent · FastAPI entrypoint

Unchanged surface API. Adds session_id for multi-turn confirmation flow.
"""

import os
from typing import Optional, List
from fastapi import FastAPI, Header
from pydantic import BaseModel
from agent import run_agent

app = FastAPI(title="ShipStack AI Tool Agent")


class ChatRequest(BaseModel):
    message: str
    history: list = []
    session_id: str = "default"   # Pass a stable ID per user/conversation


class ChatResponse(BaseModel):
    response: str
    tools_used: List[str]
    awaiting_confirmation: bool = False
    confirmation_prompt: Optional[str] = None


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    result = await run_agent(
        message=req.message,
        history=req.history,
        session_id=req.session_id,
    )
    return ChatResponse(**result)


@app.get("/")
async def root():
    return {"message": "AI Tool Agent is running"}


@app.get("/health")
async def health():
    return {"status": "ok"}
