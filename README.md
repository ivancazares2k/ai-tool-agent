# AI Tool Agent

A personal AI assistant that can take real actions — searching the web, reading GitHub repositories, creating issues, and managing long-term memory.

## What Makes This Different

Most AI chatbots only generate text. This agent uses Claude's tool calling API to actually *do things*. When you ask about AI salaries, it searches the web in real time. When you ask about your repos, it calls the GitHub API. When you share something important, it saves it to a vector memory database.

## Tools

- **Web Search** — Brave Search API for real-time web results
- **Memory** — Save and retrieve information using vector embeddings and semantic search
- **GitHub** — List repositories and create issues

## How Tool Calling Works

You send a message → Claude decides which tool to use and with what arguments → your backend executes the tool → the result goes back to Claude → Claude responds with real data.

Claude makes all tool decisions autonomously based on context. You never specify which tool to use — it figures it out.

## Tech Stack

**Backend**
- FastAPI — async Python web framework
- Anthropic Claude API — tool calling and reasoning
- Brave Search API — real-time web search
- Supabase + pgvector — vector memory storage
- Ollama + nomic-embed-text — local embeddings
- PyGithub — GitHub API integration

**Frontend**
- React + Vite
- Shows which tools were used for each response

## Running Locally

### Prerequisites
- Python 3.9+
- Node.js 18+
- Anthropic API key
- Brave Search API key
- GitHub personal access token
- Supabase project with pgvector
- Ollama running locally

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` in `backend/`:
```
ANTHROPIC_API_KEY=your_key
BRAVE_API_KEY=your_key
GITHUB_TOKEN=your_token
SUPABASE_URL=your_url
SUPABASE_KEY=your_key
OLLAMA_URL=http://localhost:11434
```

```bash
python3 -m uvicorn main:app --reload --port 8002
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## What I Learned

- Anthropic's tool use API and how to define tool schemas
- Agentic loops — how Claude decides when and which tools to call
- Chaining multiple tool calls in a single conversation turn
- Integrating multiple external APIs into one agent
- The difference between text generation and action-taking AI systems

## Author

Built by Ivan Cazares as a portfolio project while transitioning into AI engineering.
