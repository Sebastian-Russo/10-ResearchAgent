"""
Think of this like sending a researcher to a library with a list of questions.
They don't just find the books — they read them and come back with notes.

The Anthropic web search tool works the same way. We give Claude a query,
it searches the web, reads the pages, and returns a summary of what it found.
We don't scrape anything ourselves — Claude handles the full search-and-read cycle.
"""

import time
import anthropic
from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL_FAST


def search(query: str) -> dict:
    """
    Run a single web search using the Anthropic web search tool.

    Returns:
      - query:   the original search query
      - content: what Claude found and summarized
      - success: whether the search returned useful results
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    print(f"  [Searcher] Searching: '{query}'")

    response = client.messages.create(
        model      = CLAUDE_MODEL_FAST,
        max_tokens = 1000,
        # This is how you give Claude tools — it decides when and how to use them
        tools      = [{"type": "web_search_20250305", "name": "web_search"}],
        messages   = [{
            "role":    "user",
            "content": f"""Search the web for information about: "{query}"

Summarize what you find in 3-5 paragraphs. Include:
- Key facts and findings
- Important names, numbers, or dates
- Any notable disagreements or competing perspectives

Be specific and factual. This summary will be used in a research report."""
        }]
    )

    # Claude's response may contain tool_use blocks (the search calls)
    # and text blocks (the summary). We want the text.
    content = ""
    for block in response.content:
        if block.type == "text":
            content += block.text

    success = bool(content.strip())

    return {
        "query":   query,
        "content": content.strip(),
        "success": success
    }


def run_searches(queries: list[str]) -> list[dict]:
    """Run searches for all queries in a round and return results."""
    results = []
    for i, query in enumerate(queries):
        result = search(query)
        if result["success"]:
            print(f"  [Searcher] ✓ Got {len(result['content'])} characters")
        else:
            print(f"  [Searcher] ✗ No content returned")
        results.append(result)

        # Pause between searches to avoid hitting rate limits
        # Deep mode fires 5 searches per round which can spike token usage
        if i < len(queries) - 1:
            print(f"  [Searcher] Waiting 3s to avoid rate limit...")
            time.sleep(3)

    return results

# The important thing to understand here is what's different from the Personal KB scraper.
# In project 9 we fetched URLs ourselves with trafilatura.
# Here Claude fetches and reads pages internally as part of its tool use — we just get back the synthesized content.
# We trade control for simplicity.
