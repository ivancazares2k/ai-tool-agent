import os
import anthropic
from dotenv import load_dotenv
from tools.search import web_search
from tools.memory import save_memory, search_memory
from tools.github_tool import create_github_issue, get_github_repos

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
    else:
        return f"Unknown tool: {tool_name}"

async def run_agent(message: str, history: list) -> dict:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    system = """You are a powerful personal AI assistant with access to tools.
You can search the web, manage memories, and interact with GitHub.

When you need current information, search the web.
When you learn something important about the user, save it to memory.
When the user asks about their past or preferences, search memory first.
When the user asks about GitHub, use the GitHub tools.

Always be direct and helpful. Use tools when they would help give a better answer."""

    messages = history + [{"role": "user", "content": message}]
    tools_used = []

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