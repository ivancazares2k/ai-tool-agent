# AI Tool Agent

A personal AI assistant that thinks before it acts. It plans complex tasks, executes them step by step using real tools, evaluates its own responses, and remembers everything across conversations.

## What Makes This Different

Most AI assistants react to your message and respond. This agent:

1. **Knows you before you speak** — automatically loads relevant memories at the start of every conversation
2. **Plans before acting** — for complex tasks, generates a step-by-step execution plan before doing anything
3. **Uses real tools** — searches the web, runs code, reads webpages, interacts with GitHub
4. **Evaluates itself** — rates every response on tool usage, completeness, and helpfulness
5. **Remembers everything** — saves important information to a vector database and retrieves it semantically
6. **Compresses memory** — periodically merges similar memories to keep the database clean and accurate

## Tools

- **Web search** — Brave Search API for real-time results
- **Memory** — save and retrieve information using vector embeddings and semantic search
- **GitHub** — list repositories, create issues
- **URL fetcher** — read and extract text from any webpage
- **Code executor** — write and run Python code, capture output
- **Text analyzer** — analyze documents, job postings, articles against your background
- **Wikipedia** — instant access to encyclopedic knowledge on any topic
- **Memory compression** — merge similar memories into clean summaries

## Intelligence Features

**Auto memory loading** — at the start of every conversation, the agent automatically searches your memory database and injects relevant context into the system prompt. Claude knows who you are before you say a word.

**Two-phase planning** — when you send a complex multi-step request, the agent first generates a numbered plan showing exactly what it will do and which tools it will use. Then it executes each step. Simple questions skip planning for speed.

**Smart tool chaining** — the agent automatically chains tools in the right order. URL + analysis triggers fetch then analyze. Web research triggers search then fetch then summarize. Calculations automatically trigger code executor.

**Self-evaluation** — after every substantial response, the agent makes a second Claude API call to score itself on three criteria: tool usage (1-10), completeness (1-10), and helpfulness (1-10). The average score appears as a quality badge in the UI. Evaluations are saved to memory with a SELF-EVAL prefix for tracking improvement over time.

**Memory compression** — a compression tool clusters similar memories using cosine similarity and merges nearly identical ones into cleaner summaries using Claude. Keeps the database lean without losing important context.

## How Planning Works

- Simple: "What are my GitHub repos?" → direct tool call, instant response
- Complex: "Research the top AI companies, analyze my fit for each, save the best opportunity to memory" → step-by-step plan generated, then executed autonomously

## Tech Stack

**Backend**
- FastAPI — async Python web framework
- Anthropic Claude API — reasoning, planning, tool use, and self-evaluation
- Brave Search API — real-time web search
- Supabase + pgvector — vector memory storage and similarity search
- Ollama + nomic-embed-text — local embeddings
- PyGithub — GitHub API integration
- httpx — async HTTP for URL fetching
- numpy — cosine similarity for memory compression

**Frontend**
- React + Vite
- Shows which tools were used and quality score for each response

## Running Locally

### Prerequisites
- Python 3.9+
- Node.js 18+
- Anthropic API key
- Brave Search API key
- GitHub personal access token
- Supabase project with pgvector enabled
- Ollama running locally with nomic-embed-text model

### Supabase Setup

Run this in your Supabase SQL editor:

```sql
create extension if not exists vector;

create table memories (
  id uuid primary key default gen_random_uuid(),
  content text not null,
  embedding vector(768),
  created_at timestamp default now()
);

create or replace function match_memories(
  query_embedding vector(768),
  match_threshold float,
  match_count int
)
returns table(id uuid, content text, similarity float)
language sql stable as $$
  select memories.id, memories.content,
    1 - (memories.embedding <=> query_embedding) as similarity
  from memories
  where 1 - (memories.embedding <=> query_embedding) > match_threshold
  order by similarity desc
  limit match_count;
$$;
```

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
python3 -m uvicorn main:app --port 8002
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
Auto memory search → inject context into system prompt
↓
Complexity check
↓
[Complex] Generate step-by-step plan → execute each step
[Simple]  Direct tool use
↓
Response generated
↓
Self-evaluate → score tool usage, completeness, helpfulness
↓
Save evaluation to memory → track improvement over time
↓
Return response + tools used + quality score

## Project Structure
ai-tool-agent/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── agent.py             # Core agent with planning and self-evaluation
│   ├── models.py            # Request models
│   ├── tools/
│   │   ├── search.py        # Brave web search
│   │   ├── memory.py        # Vector memory + compression
│   │   ├── github_tool.py   # GitHub API
│   │   ├── url_fetcher.py   # Webpage reader
│   │   ├── code_executor.py # Python runner
│   │   ├── analyze_text.py  # Text analysis
│   │   └── wikipedia.py     # Wikipedia search
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.jsx          # Chat UI with tool badges and quality scores
│       └── App.css
└── README.md

## What I Learned

- Anthropic tool use API and tool schema design
- Agentic loops — how Claude decides when and which tools to call
- Two-phase planning architecture for complex multi-step tasks
- Automatic context injection from vector memory
- Cosine similarity for memory clustering and compression
- Self-evaluation loops for autonomous quality improvement
- Integrating multiple external APIs into one autonomous system
- Using Claude Code to build tools faster while maintaining understanding

## Author

Built by Ivan Cazares as a portfolio project while transitioning into AI engineering.