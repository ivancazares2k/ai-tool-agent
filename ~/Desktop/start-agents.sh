#!/bin/bash

echo "Starting AI Tool Agent backend..."
osascript -e 'tell application "Terminal" to do script "cd ~/Desktop/ai-tool-agent/backend && source .venv/bin/activate && python3 -m uvicorn main:app --port 8002"'

echo "Starting AI Tool Agent frontend..."
osascript -e 'tell application "Terminal" to do script "cd ~/Desktop/ai-tool-agent/frontend && npm run dev"'

echo "Starting AI Memory Agent backend..."
osascript -e 'tell application "Terminal" to do script "cd ~/Desktop/ai-memory-agent/backend && source .venv/bin/activate && uvicorn main:app --reload --port 8001"'

echo "Done. Check Terminal windows for startup status."