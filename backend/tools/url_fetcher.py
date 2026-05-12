import httpx
import re


async def fetch_url(url: str) -> str:
    """
    Fetch content from a URL and return clean text.
    
    Args:
        url: The URL to fetch content from
    
    Returns:
        The first 3000 characters of clean text from the page
    """
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            # Get the HTML content
            html_content = response.text
            
            # Strip HTML tags using regex
            # Remove script and style elements
            html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', '', html_content)
            
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
            
            # Return first 3000 characters
            return text[:3000] if len(text) > 3000 else text
            
    except httpx.HTTPError as e:
        return f"Error fetching URL: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
