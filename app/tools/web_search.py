"""
Aletheia — Web Search Tool
Uses Tavily (free for 1000 requests, requires API Key).
"""
import httpx

from app.config import get_settings

TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "The search query"
        },
        "max_results": {
            "type": "integer",
            "description": "Number of results to return (1-5). Default 3.",
        }
    },
    "required": ["query"]
}

_TAVILY_URL = "https://api.tavily.com/search"


async def web_search(args: dict) -> dict:
    query: str = args.get("query", "")
    max_results: int = args.get("max_results", 3)
    api_key = get_settings().tavily_api_key

    if not api_key:
        return {"error": "Tavily API key not configured."}

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            _TAVILY_URL,
            json={"api_key": api_key, "query": query, "max_results": max_results},
        )
        resp.raise_for_status()
        data = resp.json()

    results = [
        {"title": r["title"], "url": r["url"], "snippet": r["content"][:300]}
        for r in data.get("results", [])
    ]

    return {
        "answer": data.get("answer"),
        "results": results,
    }