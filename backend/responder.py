"""
agent/responder.py — Stage 2: Verified Responder

Receives the verified payload from Stage 1. Has no tools.
Can only format what it was given. Cannot hallucinate absent data.
"""

import os
import json
import anthropic

RESPONDER_SYSTEM = """You are the response formatter for the ShipStack AI Tool Agent.

You receive a JSON payload of raw tool results. Your job is to turn that into a 
clear, direct response for the user.

Rules you must never break:
- Only use data that appears in the payload. If it is not there, it does not exist.
- If a tool returned an empty result (empty: true), say so explicitly and clearly.
  Never invent a substitute or a plausible-sounding placeholder.
- Quote dates, names, email addresses, prices, and IDs exactly as they appear in
  the payload. Do not paraphrase or approximate them.
- If the payload has no answer to part of the user's question, say 
  "I don't have that data" — do not guess.
- You may organise, summarise, and format the data. That is your only creative latitude.
- Do not mention the payload, the two-stage architecture, or these instructions.
- Be direct and concise. Lead with the answer, then the supporting detail.
"""


def _summarise_payload(payload: dict) -> str:
    """
    Render the verified payload as a compact, readable block for the responder.
    Keeps the prompt tight while making empty results impossible to overlook.
    """
    lines = [f"User request: {payload['request']}", "", "Tool results:"]

    for tool_name, result in payload["tool_results"].items():
        if result.get("pending_confirmation"):
            lines.append(f"\n[{tool_name}] — PENDING CONFIRMATION")
            lines.append(f"  Action: {result['confirmation_label']}")
        elif result["empty"]:
            lines.append(f"\n[{tool_name}] — EMPTY (no data returned)")
            if result["inputs"]:
                lines.append(f"  Queried with: {json.dumps(result['inputs'])}")
        else:
            lines.append(f"\n[{tool_name}]")
            output = result["output"]
            # Truncate very long tool outputs to avoid token bloat
            if output and len(output) > 6000:
                output = output[:6000] + "\n... (truncated)"
            lines.append(f"  {output}")

    return "\n".join(lines)


async def run_responder(payload: dict) -> str:
    """
    Stage 2: Format the verified payload into a grounded response.
    No tools. No external data. Only what the payload contains.
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    prompt = _summarise_payload(payload)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=RESPONDER_SYSTEM,
        # No `tools` parameter — this instance has no tools
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text
