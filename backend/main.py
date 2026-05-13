from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from agent import run_agent
from models import ChatRequest

load_dotenv()

app = FastAPI(title="AI Tool Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

conversation_history = []

@app.get("/")
async def root():
    return {"message": "AI Tool Agent is running"}

@app.post("/chat")
async def chat(request: ChatRequest):
    global conversation_history

    result = await run_agent(request.message, conversation_history)

    conversation_history.append({"role": "user", "content": request.message})
    conversation_history.append({"role": "assistant", "content": result["response"]})

    return {
        "response": result["response"],
        "tools_used": result["tools_used"],
        "evaluation_score": result.get("evaluation_score")
    }

@app.delete("/history")
async def clear_history():
    global conversation_history
    conversation_history = []
    return {"message": "History cleared"}