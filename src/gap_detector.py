"""
Think of this like a fact-checker reviewing a draft article.
They read what the reporter wrote and ask:
"What questions does a reader still have after reading this?
What did we promise to cover but didn't? What's still unclear?"

Those unanswered questions are the gaps.
This file does the same — reads all research so far and identifies
what's still missing before deciding whether to search again.
"""

import json
import anthropic
from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL_FAST, GAP_THRESHOLD


def detect_gaps(topic: str, research_so_far: list[dict]) -> list[str]:
    """
    Read all research collected so far and identify what's still missing.

    Returns a list of gap descriptions. Empty list means research is complete.
    If fewer than GAP_THRESHOLD gaps found, the agent stops early.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Summarize what we have so far for the prompt
    research_summary = "\n\n".join(
        f"Search: '{r['query']}'\nFindings: {r['content'][:500]}..."
        for r in research_so_far
        if r["success"]
    )

    prompt = f"""You are evaluating research completeness on this topic:
Topic: "{topic}"

Research collected so far:
{research_summary}

Identify gaps — important aspects of this topic that are NOT yet covered
or are covered too superficially to include in a report.

Rules:
- Only list genuine gaps, not minor details
- Be specific about what's missing (e.g. "no data on costs" not just "more detail needed")
- If the research is comprehensive, return an empty list
- Maximum 5 gaps

Respond with ONLY a JSON array of strings. No explanation, no markdown.
Example: ["gap one", "gap two"] or [] if complete."""

    response = client.messages.create(
        model      = CLAUDE_MODEL_FAST,
        max_tokens = 200,
        messages   = [{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        gaps = json.loads(raw)
        if not isinstance(gaps, list):
            raise ValueError("Expected a list")
        gaps = [str(g) for g in gaps]
        print(f"  [GapDetector] Found {len(gaps)} gaps")
        for g in gaps:
            print(f"  [GapDetector] Gap: {g}")
        return gaps
    except (json.JSONDecodeError, ValueError):
        print(f"  [GapDetector] JSON parse failed. Raw: {raw}")
        return []


def is_research_complete(gaps: list[str]) -> bool:
    """
    Decide whether to stop researching based on gap count.
    Below GAP_THRESHOLD means close enough — stop and write the report.
    """
    return len(gaps) < GAP_THRESHOLD
