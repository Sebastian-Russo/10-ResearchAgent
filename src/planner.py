"""
Think of this like a journalist's assignment editor.
Before sending reporters out, the editor looks at the topic
and decides: "We need someone covering the science angle,
someone on the economics, and someone tracking recent news."

Each angle becomes a targeted search query.
On later rounds, the editor also looks at what reporters
already found and decides what's still missing.

Improvement:
Think of this like a journalist's assignment editor who keeps
a running list of every story already filed. They never assign
the same story twice, and when gaps are critical they prioritize
those angles first.
"""

import json
import anthropic
from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL_FAST, SEARCHES_PER_ROUND


def generate_queries(
    topic:       str,
    gaps:        list[dict] = None,
    round_num:   int        = 1,
    past_queries: list[str] = None
) -> list[str]:
    """
    Generate search queries for the current round.

    Round 1: broad queries covering main angles
    Round 2+: targeted queries aimed at critical gaps first,
              never repeating past queries
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Build the "already searched" context
    past_text = ""
    if past_queries:
        past_text = "\n\nQueries already run — do NOT repeat these angles:\n" + \
                    "\n".join(f"- {q}" for q in past_queries)

    if round_num == 1 or not gaps:
        prompt = f"""You are a research planner. Generate {SEARCHES_PER_ROUND} search queries
to research this topic comprehensively:

Topic: "{topic}"
{past_text}

Rules:
- Cover different angles: background, current state, key players, recent developments
- Each query should be specific enough to find useful results
- Phrase as real search engine queries (short, keyword-focused)
- Never duplicate past queries

Respond with ONLY a JSON array of strings. No explanation, no markdown.
Example: ["query one", "query two", "query three"]"""

    else:
        # Sort gaps by severity — tackle critical ones first
        sorted_gaps = sorted(gaps, key=lambda g: g["severity"], reverse=True)
        gaps_text   = "\n".join(
            f"- [severity {g['severity']}] {g['description']}"
            for g in sorted_gaps
        )

        prompt = f"""You are a research planner. We are researching "{topic}".

Remaining gaps ranked by severity (3=critical, 2=important, 1=minor):
{gaps_text}
{past_text}

Generate {SEARCHES_PER_ROUND} search queries targeting the CRITICAL gaps first,
then important gaps if space remains. Ignore minor gaps.

Rules:
- Never repeat past queries or search the same angle twice
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
