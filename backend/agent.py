"""
agent.py — ShipStack AI Tool Agent (two-stage architecture)

Replaces the original monolithic agent.py.

Stage 1 (executor)  → calls tools, produces a verified payload of raw results
Stage 2 (responder) → reads only the payload, formats a grounded response

The confirmation flow for write actions (push_file, send_email, etc.) is
preserved: Stage 1 detects the write action, pauses the loop, and returns a
pending_write descriptor. The orchestrator surfaces the confirmation prompt to
the user. On "confirm", it executes the write and runs Stage 2 on the result.
"""

import os
from typing import Optional, List
from dotenv import load_dotenv
from tools.memory import search_memory
from executor import run_executor, execute_confirmed_write
from responder import run_responder

load_dotenv()

# ---------------------------------------------------------------------------
# Pending write state (in-memory; swap for Redis/DB in production)
# ---------------------------------------------------------------------------
# Keyed by a session/user identifier. For a single-user CLI agent, one slot
# is enough. For multi-user FastAPI, key by user_id or session_id.

_pending_writes: dict = {}  # { session_id: pending_write_dict }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def run_agent(message: str, history: list, session_id: str = "default") -> dict:
    """
    Run the two-stage pipeline and return:
    {
        "response": str,
        "tools_used": [str],
        "awaiting_confirmation": bool,
        "confirmation_prompt": str | None,
    }
    """

    # --- Handle a "confirm" reply for a pending write action ---
    if message.strip().lower() in ("confirm", "yes", "y", "proceed") and session_id in _pending_writes:
        pending = _pending_writes.pop(session_id)
        payload = await execute_confirmed_write(pending)
        response_text = await run_responder(payload)
        return {
            "response": response_text,
            "tools_used": payload["tools_called"],
            "awaiting_confirmation": False,
            "confirmation_prompt": None,
        }

    # --- Normal request ---

    # Fetch memory context before Stage 1 (read-only, outside the tool loop)
    memory_context: Optional[str] = None
    if not history:
        memory_context = await search_memory(message[:100])

    # Stage 1: collect tool results
    payload = await run_executor(
        user_request=message,
        history=history,
        memory_context=memory_context,
    )

    # Write action detected — pause and ask the user to confirm
    if payload["pending_write"]:
        _pending_writes[session_id] = payload["pending_write"]
        label = payload["pending_write"]["label"]
        return {
            "response": f"⚠️ I'm about to **{label}**. Reply `confirm` to proceed or anything else to cancel.",
            "tools_used": payload["tools_called"],
            "awaiting_confirmation": True,
            "confirmation_prompt": label,
        }

    # Stage 2: format into a grounded response
    response_text = await run_responder(payload)

    return {
        "response": response_text,
        "tools_used": payload["tools_called"],
        "awaiting_confirmation": False,
        "confirmation_prompt": None,
    }
