"""
executor.py — Stage 1: Tool Executor

Runs the agentic tool-calling loop. Produces a verified payload of raw tool
results. Never generates prose. Never completes missing data.

Preserves your existing confirmation gate for write actions.
"""

import os
import json
from typing import Optional, List, Dict
import anthropic
from tools.search import web_search
from tools.memory import save_memory, search_memory, compress_memories
from tools.github_tool import (
    get_repo_structure, read_file, push_file,
    create_pr, list_issues, create_issue
)
from tools.analyze_text import analyze_text
from tools.url_fetcher import fetch_url
from tools.gmail import (
    get_emails, draft_email, send_email,
    get_email_body, search_emails, reply_to_email,
    mark_as_read
)
from tools.code_executor import execute_code
from tools.wikipedia import search_wikipedia
from tools.gumroad_tool import (
    get_products, get_product, create_product,
    update_product, enable_product, disable_product,
    get_sales, get_sale
)

# ---------------------------------------------------------------------------
# Tool schema (unchanged from your original agent.py)
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "web_search",
        "description": "Search the web for current information on any topic.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "The search query"}},
            "required": ["query"]
        }
    },
    {
        "name": "save_memory",
        "description": "Save important information to long-term memory for future reference.",
        "input_schema": {
            "type": "object",
            "properties": {"content": {"type": "string", "description": "The information to save to memory"}},
            "required": ["content"]
        }
    },
    {
        "name": "search_memory",
        "description": "Search long-term memory for relevant information about the user or past conversations.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "What to search for in memory"}},
            "required": ["query"]
        }
    },
    {
        "name": "get_repo_structure",
        "description": "List the file and folder structure of a GitHub repository.",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo_name": {"type": "string", "description": "Full repo name in owner/repo format"},
                "path": {"type": "string", "description": "Subdirectory path to list (defaults to root)"}
            },
            "required": ["repo_name"]
        }
    },
    {
        "name": "read_file",
        "description": "Read the contents of a file from a GitHub repository.",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo_name": {"type": "string"},
                "file_path": {"type": "string"},
                "branch": {"type": "string", "description": "Branch to read from (defaults to main)"}
            },
            "required": ["repo_name", "file_path"]
        }
    },
    {
        "name": "push_file",
        "description": "Create or update a file directly in a GitHub repository.",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo_name": {"type": "string"},
                "file_path": {"type": "string"},
                "content": {"type": "string"},
                "commit_message": {"type": "string"},
                "branch": {"type": "string"}
            },
            "required": ["repo_name", "file_path", "content", "commit_message"]
        }
    },
    {
        "name": "create_pr",
        "description": "Open a pull request in a GitHub repository.",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo_name": {"type": "string"},
                "title": {"type": "string"},
                "body": {"type": "string"},
                "head_branch": {"type": "string"},
                "base_branch": {"type": "string"}
            },
            "required": ["repo_name", "title", "body", "head_branch"]
        }
    },
    {
        "name": "list_issues",
        "description": "List issues in a GitHub repository.",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo_name": {"type": "string"},
                "state": {"type": "string", "description": "open, closed, or all (defaults to open)"}
            },
            "required": ["repo_name"]
        }
    },
    {
        "name": "create_issue",
        "description": "Create a new issue in a GitHub repository.",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo_name": {"type": "string"},
                "title": {"type": "string"},
                "body": {"type": "string"}
            },
            "required": ["repo_name", "title"]
        }
    },
    {
        "name": "analyze_text",
        "description": "Analyze text content based on a specified task.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "task": {"type": "string", "description": "What to do with the text (defaults to summarize)"}
            },
            "required": ["content"]
        }
    },
    {
        "name": "fetch_url",
        "description": "Fetch and extract clean text content from a URL.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"]
        }
    },
    {
        "name": "get_emails",
        "description": "Fetch recent emails from Gmail inbox.",
        "input_schema": {
            "type": "object",
            "properties": {
                "max_results": {"type": "integer"},
                "unread_only": {"type": "boolean"}
            },
            "required": []
        }
    },
    {
        "name": "read_email",
        "description": "Read the full content of a specific email by its ID.",
        "input_schema": {
            "type": "object",
            "properties": {"message_id": {"type": "string"}},
            "required": ["message_id"]
        }
    },
    {
        "name": "search_emails",
        "description": "Search Gmail using any Gmail search query string.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "max_results": {"type": "integer"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "draft_email",
        "description": "Save an email as a draft in Gmail without sending it.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"}
            },
            "required": ["to", "subject", "body"]
        }
    },
    {
        "name": "send_email",
        "description": "Send an email via Gmail.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"}
            },
            "required": ["to", "subject", "body"]
        }
    },
    {
        "name": "reply_email",
        "description": "Reply to an existing email thread.",
        "input_schema": {
            "type": "object",
            "properties": {
                "message_id": {"type": "string"},
                "body": {"type": "string"}
            },
            "required": ["message_id", "body"]
        }
    },
    {
        "name": "mark_as_read",
        "description": "Mark an email as read by its ID.",
        "input_schema": {
            "type": "object",
            "properties": {"message_id": {"type": "string"}},
            "required": ["message_id"]
        }
    },
    {
        "name": "execute_code",
        "description": "Execute Python code safely with a 10 second timeout.",
        "input_schema": {
            "type": "object",
            "properties": {"python_code": {"type": "string"}},
            "required": ["python_code"]
        }
    },
    {
        "name": "search_wikipedia",
        "description": "Search Wikipedia and return a summary of the top result.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"]
        }
    },
    {
        "name": "compress_memory",
        "description": "Compress similar memories by clustering and merging them using AI.",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_products",
        "description": "Retrieve all products in the Gumroad store.",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_product",
        "description": "Retrieve full details for a single Gumroad product by ID.",
        "input_schema": {
            "type": "object",
            "properties": {"product_id": {"type": "string"}},
            "required": ["product_id"]
        }
    },
    {
        "name": "create_product",
        "description": "Create a new product listing on Gumroad.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "price_cents": {"type": "integer"},
                "description": {"type": "string"}
            },
            "required": ["name", "price_cents"]
        }
    },
    {
        "name": "update_product",
        "description": "Update an existing Gumroad product.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string"},
                "name": {"type": "string"},
                "price_cents": {"type": "integer"},
                "description": {"type": "string"}
            },
            "required": ["product_id"]
        }
    },
    {
        "name": "enable_product",
        "description": "Publish a Gumroad product so it is live and purchasable.",
        "input_schema": {
            "type": "object",
            "properties": {"product_id": {"type": "string"}},
            "required": ["product_id"]
        }
    },
    {
        "name": "disable_product",
        "description": "Unpublish a Gumroad product so it is no longer purchasable.",
        "input_schema": {
            "type": "object",
            "properties": {"product_id": {"type": "string"}},
            "required": ["product_id"]
        }
    },
    {
        "name": "get_sales",
        "description": "Retrieve recent sales data from the Gumroad store.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string"},
                "after": {"type": "string"},
                "before": {"type": "string"},
                "max_results": {"type": "integer"}
            },
            "required": []
        }
    },
    {
        "name": "get_sale",
        "description": "Retrieve full details for a single Gumroad sale by ID.",
        "input_schema": {
            "type": "object",
            "properties": {"sale_id": {"type": "string"}},
            "required": ["sale_id"]
        }
    }
]

# ---------------------------------------------------------------------------
# Write-action confirmation gate (preserved from your original)
# ---------------------------------------------------------------------------

WRITE_ACTIONS = {
    "push_file", "create_pr", "send_email", "reply_email",
    "create_product", "enable_product", "disable_product", "update_product"
}

WRITE_ACTION_LABELS = {
    "push_file":       lambda i: f"push file '{i.get('file_path')}' to {i.get('repo_name')}",
    "create_pr":       lambda i: f"create PR '{i.get('title')}' in {i.get('repo_name')}",
    "send_email":      lambda i: f"send email to {i.get('to')} — subject: '{i.get('subject')}'",
    "reply_email":     lambda i: f"reply to email {i.get('message_id')}",
    "create_product":  lambda i: f"create Gumroad product '{i.get('name')}' at ${i.get('price_cents', 0)/100:.2f}",
    "enable_product":  lambda i: f"publish Gumroad product {i.get('product_id')}",
    "disable_product": lambda i: f"unpublish Gumroad product {i.get('product_id')}",
    "update_product":  lambda i: f"update Gumroad product {i.get('product_id')}",
}

# ---------------------------------------------------------------------------
# Tool dispatcher (unchanged logic from your original execute_tool)
# ---------------------------------------------------------------------------

async def _dispatch(tool_name: str, tool_input: dict) -> str:
    """Execute a single tool and return its raw string result."""
    if tool_name == "web_search":
        return await web_search(tool_input["query"])
    elif tool_name == "save_memory":
        return await save_memory(tool_input["content"])
    elif tool_name == "search_memory":
        return await search_memory(tool_input["query"])
    elif tool_name == "get_repo_structure":
        return await get_repo_structure(tool_input["repo_name"], tool_input.get("path", ""))
    elif tool_name == "read_file":
        return await read_file(tool_input["repo_name"], tool_input["file_path"], tool_input.get("branch", "main"))
    elif tool_name == "push_file":
        return await push_file(
            tool_input["repo_name"], tool_input["file_path"],
            tool_input["content"], tool_input["commit_message"],
            tool_input.get("branch", "main")
        )
    elif tool_name == "create_pr":
        return await create_pr(
            tool_input["repo_name"], tool_input["title"],
            tool_input["body"], tool_input["head_branch"],
            tool_input.get("base_branch", "main")
        )
    elif tool_name == "list_issues":
        return await list_issues(tool_input["repo_name"], tool_input.get("state", "open"))
    elif tool_name == "create_issue":
        return await create_issue(tool_input["repo_name"], tool_input["title"], tool_input.get("body", ""))
    elif tool_name == "analyze_text":
        return await analyze_text(tool_input["content"], tool_input.get("task", "summarize"))
    elif tool_name == "fetch_url":
        return await fetch_url(tool_input["url"])
    elif tool_name == "get_emails":
        return await get_emails(tool_input.get("max_results", 10), tool_input.get("unread_only", True))
    elif tool_name == "read_email":
        return await get_email_body(tool_input["message_id"])
    elif tool_name == "search_emails":
        return await search_emails(tool_input["query"], tool_input.get("max_results", 10))
    elif tool_name == "draft_email":
        return await draft_email(tool_input["to"], tool_input["subject"], tool_input["body"])
    elif tool_name == "send_email":
        return await send_email(tool_input["to"], tool_input["subject"], tool_input["body"])
    elif tool_name == "reply_email":
        return await reply_to_email(tool_input["message_id"], tool_input["body"])
    elif tool_name == "mark_as_read":
        return await mark_as_read(tool_input["message_id"])
    elif tool_name == "execute_code":
        return await execute_code(tool_input["python_code"])
    elif tool_name == "search_wikipedia":
        return await search_wikipedia(tool_input["query"])
    elif tool_name == "compress_memory":
        return await compress_memories()
    elif tool_name == "get_products":
        return await get_products()
    elif tool_name == "get_product":
        return await get_product(tool_input["product_id"])
    elif tool_name == "create_product":
        return await create_product(tool_input["name"], tool_input["price_cents"], tool_input.get("description", ""))
    elif tool_name == "update_product":
        return await update_product(
            tool_input["product_id"],
            tool_input.get("name", ""),
            tool_input.get("price_cents", -1),
            tool_input.get("description", "")
        )
    elif tool_name == "enable_product":
        return await enable_product(tool_input["product_id"])
    elif tool_name == "disable_product":
        return await disable_product(tool_input["product_id"])
    elif tool_name == "get_sales":
        return await get_sales(
            tool_input.get("product_id", ""),
            tool_input.get("after", ""),
            tool_input.get("before", ""),
            tool_input.get("max_results", 10)
        )
    elif tool_name == "get_sale":
        return await get_sale(tool_input["sale_id"])
    else:
        return f"ERROR: Unknown tool '{tool_name}'"

# ---------------------------------------------------------------------------
# Stage 1 system prompt
# ---------------------------------------------------------------------------

EXECUTOR_SYSTEM = """You are the tool executor for the ShipStack AI Tool Agent.

YOUR ONLY JOB: Call the tools needed to answer the user's request. Collect raw results.

Rules you must never break:
- Call every tool needed to satisfy the request
- ALWAYS search_memory first on personal questions about the user
- ALWAYS use web_search for current events or recent information
- For tool chaining (e.g. fetch_url → analyze_text), call them in sequence
- Never write prose, summaries, explanations, or interpretations
- Never invent, infer, or complete missing data
- If a tool returns empty, record it as empty — do not substitute
- Stop when all needed tools have been called. Do not generate a final response.
"""

# ---------------------------------------------------------------------------
# Stage 1 entry point
# ---------------------------------------------------------------------------

async def run_executor(
    user_request: str,
    history: list,
    memory_context: Optional[str] = None,
) -> dict:
    """
    Run the tool-calling loop. Returns a verified payload:
    {
        "request": str,
        "tool_results": {
            tool_name: {
                "inputs": dict,
                "output": str,           # raw string from the tool
                "empty": bool,           # True when output is empty/None/"No X found."
                "pending_confirmation": bool,  # True for blocked write actions
                "confirmation_label": str,     # Human-readable description of the action
            }
        },
        "tools_called": [str],
        "pending_write": dict | None,    # Set if a write action is waiting for confirm
    }
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    system = EXECUTOR_SYSTEM
    if memory_context and memory_context != "No memories found.":
        system += f"\n\n--- USER CONTEXT FROM MEMORY ---\n{memory_context}\n--- END CONTEXT ---"

    messages = history + [{"role": "user", "content": user_request}]

    tool_results: dict = {}
    tools_called: list = []
    pending_write: Optional[dict] = None

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system,
            tools=TOOLS,
            messages=messages,
        )

        # Collect tool_use blocks from this turn
        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

        # No more tool calls → executor is done
        if not tool_use_blocks:
            break

        # Process each tool call
        tool_result_blocks = []
        for block in tool_use_blocks:
            name = block.name
            inputs = block.input
            tools_called.append(name)

            # --- Confirmation gate for write actions ---
            if name in WRITE_ACTIONS:
                label = WRITE_ACTION_LABELS.get(name, lambda i: name)(inputs)
                tool_results[name] = {
                    "inputs": inputs,
                    "output": None,
                    "empty": True,
                    "pending_confirmation": True,
                    "confirmation_label": label,
                }
                pending_write = {
                    "tool_name": name,
                    "inputs": inputs,
                    "tool_use_id": block.id,
                    "label": label,
                }
                # Feed a blocked result back so Claude knows to stop
                tool_result_blocks.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": f"BLOCKED: Awaiting user confirmation to {label}.",
                })
                continue

            # --- Normal read tool ---
            print(f"  [executor] calling {name}")
            raw = await _dispatch(name, inputs)
            is_empty = not raw or raw.strip() in (
                "", "No memories found.", "No emails found.", "No results.", "[]", "{}"
            )
            tool_results[name] = {
                "inputs": inputs,
                "output": raw,
                "empty": is_empty,
                "pending_confirmation": False,
                "confirmation_label": None,
            }
            tool_result_blocks.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": raw if raw else "(empty result)",
            })

        # If a write action was blocked, stop the loop — need user confirmation
        if pending_write:
            break

        # Feed results back and continue the loop
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_result_blocks})

    return {
        "request": user_request,
        "tool_results": tool_results,
        "tools_called": tools_called,
        "pending_write": pending_write,
    }


async def execute_confirmed_write(pending_write: dict) -> dict:
    """
    Execute a write action after user confirmation.
    Returns a mini verified payload for the responder.
    """
    name = pending_write["tool_name"]
    inputs = pending_write["inputs"]

    print(f"  [executor] confirmed write: {name}")
    raw = await _dispatch(name, inputs)

    return {
        "request": f"Confirmed: {pending_write['label']}",
        "tool_results": {
            name: {
                "inputs": inputs,
                "output": raw,
                "empty": not bool(raw),
                "pending_confirmation": False,
                "confirmation_label": None,
            }
        },
        "tools_called": [name],
        "pending_write": None,
    }
