"""
Think of this like a journalist's assignment editor.
Before sending reporters out, the editor looks at the topic
and decides: "We need someone covering the science angle,
someone on the economics, and someone tracking recent news."

Each angle becomes a targeted search query.
On later rounds, the editor also looks at what reporters
already found and decides what's still missing.
"""

import json
import anthropic
from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL_FAST, SEARCHES_PER_ROUND


def generate_queries(topic: str, gaps: list[str] = None, round_num: int = 1) -> list[str]:
    """
    Generate search queries for the current research round.

    Round 1: broad queries covering main angles of the topic
    Round 2+: targeted queries aimed at filling specific gaps
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    if round_num == 1 or not gaps:
        prompt = f"""You are a research planner. Generate {SEARCHES_PER_ROUND} search queries
to research this topic comprehensively:

Topic: "{topic}"

Rules:
- Cover different angles: background, current state, key players, recent developments
- Each query should be specific enough to find useful results
- Phrase as real search engine queries (short, keyword-focused)

Respond with ONLY a JSON array of strings. No explanation, no markdown.
Example: ["query one", "query two", "query three"]"""

    else:
        gaps_text = "\n".join(f"- {g}" for g in gaps)
        prompt = f"""You are a research planner. We are researching "{topic}" and have
identified these gaps in our current knowledge:

{gaps_text}

Generate {SEARCHES_PER_ROUND} search queries specifically targeting these gaps.

Rules:
- Each query should directly address one or more gaps
- Be specific — broad queries already ran in earlier rounds
- Phrase as real search engine queries

Respond with ONLY a JSON array of strings. No explanation, no markdown."""

    response = client.messages.create(
        model      = CLAUDE_MODEL_FAST,
        max_tokens = 200,
        messages   = [{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        queries = json.loads(raw)
        if not isinstance(queries, list):
            raise ValueError("Expected a list")
        return [str(q) for q in queries[:SEARCHES_PER_ROUND]]
    except (json.JSONDecodeError, ValueError):
        print(f"[Planner] JSON parse failed. Raw: {raw}")
        return [topic]
