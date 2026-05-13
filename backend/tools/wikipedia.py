import httpx
import urllib.parse


async def search_wikipedia(query: str) -> str:
    """
    Search Wikipedia and return a summary of the top result.
    
    Args:
        query: The search query
    
    Returns:
        A formatted string with title, summary, and URL
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # First, search for the article
            search_url = "https://en.wikipedia.org/w/api.php"
            search_params = {
                "action": "opensearch",
                "search": query,
                "limit": 1,
                "format": "json"
            }
            
            search_response = await client.get(search_url, params=search_params)
            search_response.raise_for_status()
            search_data = search_response.json()
            
            # Check if we got results
            if not search_data[1] or len(search_data[1]) == 0:
                return f"No Wikipedia articles found for '{query}'."
            
            # Get the title of the top result
            title = search_data[1][0]
            
            # URL encode the title for the API request
            encoded_title = urllib.parse.quote(title.replace(" ", "_"))
            
            # Fetch the summary
            summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
            summary_response = await client.get(summary_url)
            summary_response.raise_for_status()
            summary_data = summary_response.json()
            
            # Extract relevant information
            article_title = summary_data.get("title", title)
            extract = summary_data.get("extract", "No summary available.")
            page_url = summary_data.get("content_urls", {}).get("desktop", {}).get("page", "")
            
            # Format the response
            result = f"""**{article_title}**

{extract}

Read more: {page_url}"""
            
            return result
    
    except httpx.HTTPError as e:
        return f"Error fetching Wikipedia article: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
