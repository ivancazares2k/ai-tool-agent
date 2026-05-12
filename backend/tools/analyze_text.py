async def analyze_text(content: str, task: str = "summarize") -> str:
    """
    Analyze text content based on the specified task.
    
    Args:
        content: The text to analyze
        task: What to do with the text (defaults to "summarize")
    
    Returns:
        A formatted string with the content and task for Claude to process
    """
    return f"""Text Analysis Request:
Task: {task}

Content to analyze:
{content}

Please perform the requested task on the content above."""
