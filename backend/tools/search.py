import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def web_search(query: str) -> str:
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": os.getenv("BRAVE_API_KEY")
    }
    params = {"q": query, "count": 5}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)
        data = response.json()

    results = data.get("web", {}).get("results", [])
    if not results:
        return "No results found."

    output = []
    for r in results[:5]:
        title = r.get("title", "")
        description = r.get("description", "")
        url_link = r.get("url", "")
        output.append(f"**{title}**\n{description}\n{url_link}")

    return "\n\n".join(output)