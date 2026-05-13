import os
import anthropic
from dotenv import load_dotenv
from tools.search import web_search
from tools.memory import save_memory, search_memory, compress_memories
from tools.github_tool import create_github_issue, get_github_repos
from tools.analyze_text import analyze_text
from tools.url_fetcher import fetch_url
from tools.gmail import get_emails, draft_email, send_email
from tools.code_executor import execute_code
from tools.wikipedia import search_wikipedia

load_dotenv()

TOOLS = [
    {
        "name": "web_search",
        "description": "Search the web for current information on any topic.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "save_memory",
        "description": "Save important information to long-term memory for future reference.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The information to save to memory"
                }
            },
            "required": ["content"]
        }
    },
    {
        "name": "search_memory",
        "description": "Search long-term memory for relevant information about the user or past conversations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to search for in memory"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "create_github_issue",
        "description": "Create a new issue in a GitHub repository.",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo_name": {
                    "type": "string",
                    "description": "The repository name in format owner/repo"
                },
                "title": {
                    "type": "string",
                    "description": "The issue title"
                },
                "body": {
                    "type": "string",
                    "description": "The issue body/description"
                }
            },
            "required": ["repo_name", "title", "body"]
        }
    },
    {
        "name": "get_github_repos",
        "description": "Get a list of the user's GitHub repositories.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "analyze_text",
        "description": "Analyze text content based on a specified task (e.g., summarize, extract key points, sentiment analysis).",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The text to analyze"
                },
                "task": {
                    "type": "string",
                    "description": "What to do with the text (defaults to 'summarize')"
                }
            },
            "required": ["content"]
        }
    },
    {
        "name": "fetch_url",
        "description": "Fetch and extract clean text content from a URL. Returns the first 3000 characters of text from the page.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to fetch content from"
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "get_emails",
        "description": "Fetch the last 10 unread emails from Gmail inbox. Returns sender, subject, and snippet for each email.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "draft_email",
        "description": "Create a draft email in Gmail.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Recipient email address"
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject"
                },
                "body": {
                    "type": "string",
                    "description": "Email body content"
                }
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
                "to": {
                    "type": "string",
                    "description": "Recipient email address"
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject"
                },
                "body": {
                    "type": "string",
                    "description": "Email body content"
                }
            },
            "required": ["to", "subject", "body"]
        }
    },
    {
        "name": "execute_code",
        "description": "Execute Python code safely with a 10 second timeout. Returns stdout and stderr output.",
        "input_schema": {
            "type": "object",
            "properties": {
                "python_code": {
                    "type": "string",
                    "description": "The Python code to execute"
                }
            },
            "required": ["python_code"]
        }
    },
    {
        "name": "search_wikipedia",
        "description": "Search Wikipedia and return a summary of the top result with title, extract, and URL.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query for Wikipedia"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "compress_memory",
        "description": "Compress similar memories by clustering and merging them using AI. Returns a report of compression results.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]

async def execute_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "web_search":
        return await web_search(tool_input["query"])
    elif tool_name == "save_memory":
        return await save_memory(tool_input["content"])
    elif tool_name == "search_memory":
        return await search_memory(tool_input["query"])
    elif tool_name == "create_github_issue":
        return await create_github_issue(
            tool_input["repo_name"],
            tool_input["title"],
            tool_input["body"]
        )
    elif tool_name == "get_github_repos":
        return await get_github_repos()
    elif tool_name == "analyze_text":
        return await analyze_text(
            tool_input["content"],
            tool_input.get("task", "summarize")
        )
    elif tool_name == "fetch_url":
        return await fetch_url(tool_input["url"])
    elif tool_name == "get_emails":
        return await get_emails()
    elif tool_name == "draft_email":
        return await draft_email(
            tool_input["to"],
            tool_input["subject"],
            tool_input["body"]
        )
    elif tool_name == "send_email":
        return await send_email(
            tool_input["to"],
            tool_input["subject"],
            tool_input["body"]
        )
    elif tool_name == "execute_code":
        return await execute_code(tool_input["python_code"])
    elif tool_name == "search_wikipedia":
        return await search_wikipedia(tool_input["query"])
    elif tool_name == "compress_memory":
        return await compress_memories()
    else:
        return f"Unknown tool: {tool_name}"

def should_plan(message: str) -> bool:
    """
    Determine if a message is complex enough to require planning.
    
    Args:
        message: The user's message
    
    Returns:
        True if the message requires planning, False otherwise
    """
    # Check for complexity indicators
    complexity_phrases = [
        "and then", "research and", "analyze and", "compare",
        "create a report", "find and", "step by step",
        "first", "second", "multiple", "several"
    ]
    
    message_lower = message.lower()
    
    # Check if message contains complexity phrases
    for phrase in complexity_phrases:
        if phrase in message_lower:
            return True
    
    # Check if message is longer than 150 characters
    if len(message) > 150:
        return True
    
    return False


async def create_plan(message: str, client, system: str) -> str:
    """
    Create a step-by-step plan for executing a complex task.
    
    Args:
        message: The user's message
        client: The Anthropic client
        system: The system prompt
    
    Returns:
        A numbered plan as a string
    """
    planning_prompt = f"""Given this user request, create a clear step-by-step plan to accomplish it. 
Break it down into numbered steps that can be executed sequentially.
Be specific about what tools or actions will be needed for each step.

User request: {message}

Respond with ONLY the numbered plan, nothing else."""

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        system=system,
        messages=[{"role": "user", "content": planning_prompt}]
    )
    
    plan = ""
    for block in response.content:
        if hasattr(block, "text"):
            plan = block.text
            break
    
    return plan


async def run_agent(message: str, history: list) -> dict:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    system = """You are a powerful personal AI assistant with access to tools.

TOOL USAGE GUIDELINES:

Memory Management:
- ALWAYS search memory FIRST before answering any personal questions about the user
- Automatically save important new information about the user to memory without being asked
- Save preferences, facts, goals, and context that would be useful in future conversations

Information Retrieval:
- ALWAYS use web_search for questions about current events, news, or recent information
- Use search_wikipedia for factual definitions, explanations of concepts, or encyclopedic information
- Use fetch_url to retrieve content from URLs the user shares

Tool Chaining:
- When the user shares a link and wants analysis: fetch_url → analyze_text
- When you need to analyze web content: web_search → fetch_url → analyze_text
- For numerical calculations or data analysis: ALWAYS use execute_code automatically

GitHub Operations:
- Use get_github_repos to list repositories
- Use create_github_issue to create issues

Email Operations:
- Use get_emails to check inbox
- Use draft_email to create drafts
- Use send_email to send messages

Planning:
- When creating execution plans, ALWAYS specify which tool will be used for each step
- Be explicit about tool chaining (e.g., "Step 1: Use web_search to find..., Step 2: Use fetch_url to retrieve...")

Always be direct, helpful, and proactive with tool usage. Use tools to give better, more accurate answers."""

    # Auto-search memory at the start of new conversations
    if not history:
        memory_context = await search_memory("user preferences information context")
        if memory_context and memory_context != "No memories found.":
            system += f"\n\n--- CONTEXT FROM MEMORY ---\n{memory_context}\n--- END CONTEXT ---"

    # Check if we need to create a plan for complex tasks
    plan = None
    if should_plan(message):
        plan = await create_plan(message, client, system)
        if plan:
            system += f"\n\n--- EXECUTION PLAN ---\n{plan}\n--- END PLAN ---\n\nFollow this plan to accomplish the user's request."

    messages = history + [{"role": "user", "content": message}]
    tools_used = []
    
    # If we created a plan, prepend it to the response
    plan_prefix = f"**Plan:**\n{plan}\n\n**Execution:**\n" if plan else ""

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4096,
            system=system,
            tools=TOOLS,
            messages=messages
        )

        if response.stop_reason == "end_turn":
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text = block.text
            
            # Prepend the plan to the final response if one was created
            if plan_prefix:
                final_text = plan_prefix + final_text
            
            return {
                "response": final_text,
                "tools_used": tools_used
            }

        if response.stop_reason == "tool_use":
            messages.append({
                "role": "assistant",
                "content": response.content
            })

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tools_used.append(block.name)
                    result = await execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

            messages.append({
                "role": "user",
                "content": tool_results
            })