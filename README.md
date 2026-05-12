# AI Tool Agent

A personal AI assistant that thinks before it acts. It plans complex tasks, executes them step by step using real tools, and remembers everything across conversations.

## What Makes This Different

Most AI assistants react to your message and respond. This agent:

1. **Knows you before you speak** — automatically loads relevant memories at the start of every conversation
2. **Plans before acting** — for complex tasks, generates a step-by-step execution plan before doing anything
3. **Uses real tools** — searches the web, runs code, reads webpages, interacts with GitHub
4. **Remembers everything** — saves important information to a vector database and retrieves it semantically

## Tools

- **Web search** — Brave Search API for real-time results
- **Memory** — save and retrieve information using vector embeddings and semantic search
- **GitHub** — list repositories, create issues
- **URL fetcher** — read and extract text from any webpage
- **Code executor** — write and run Python code, capture output
- **Text analyzer** — analyze documents, job postings, articles against your background

## How Planning Works

When you send a complex multi-step request, the agent first generates a numbered plan showing exactly what it will do and which tools it will use. Then it executes each step, passing results forward. Simple questions skip planning entirely for speed.

Example:
- Simple: "What are my GitHub repos?" → direct tool call, instant response
- Complex: "Research the top AI companies, analyze my fit for each, save the best opportunity to memory" → 11-step plan generated, then executed autonomously

## How Memory Works

Every conversation starts with an automatic memory search. Before Claude reads your message, the agent searches your memory database for relevant context about you and injects it into the system prompt. Claude wakes up knowing who you are, what you've built, and what your goals are.

## Tech Stack

**Backend**
- FastAPI — async Python web framework
- Anthropic Claude API — reasoning, planning, and tool use
- Brave Search API — real-time web search
- Supabase + pgvector — vector memory storage
- Ollama + nomic-embed-text — local embeddings
- PyGithub — GitHub API
- httpx — URL fetching

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
- Ollama running locally with nomic-embed-text

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
SUPABASE_URL=https://your-project.supabase.co
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

## Architecture
User message
↓
Auto memory search (inject context)
↓
Complexity check
↓
[Complex] Generate plan → Execute steps → Synthesize
[Simple]  Direct tool use → Respond
↓
Save important info to memory
↓
Response with tools used
## What I Learned

- Anthropic tool use API and tool schema design
- Agentic loops and multi-step execution
- Two-phase planning architecture for complex tasks
- Automatic context injection from vector memory
- Integrating multiple external APIs into one autonomous system
- Using Claude Code to build tools faster while maintaining understanding

## Author

Built by Ivan Cazares as a portfolio project while transitioning into AI engineering.
