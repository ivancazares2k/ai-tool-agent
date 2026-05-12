import httpx

async def web_search(query: str) -> str:
    url = "https://api.duckduckgo.com/"
    params = {
        "q": query,
        "format": "json",
        "no_html": "1",
        "skip_disambig": "1"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()

    results = []

    if data.get("AbstractText"):
        results.append(f"**Summary**\n{data['AbstractText']}\n{data.get('AbstractURL', '')}")

    for topic in data.get("RelatedTopics", [])[:4]:
        if isinstance(topic, dict) and topic.get("Text"):
            results.append(f"- {topic['Text']}")

    if not results:
        return "No results found for that query."

    return "\n\n".join(results)