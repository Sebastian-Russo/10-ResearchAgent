"""
Think of this like a fact-checker reviewing a draft article.
They read what the reporter wrote and ask:
"What questions does a reader still have after reading this?
What did we promise to cover but didn't? What's still unclear?"

Those unanswered questions are the gaps.
This file does the same — reads all research so far and identifies
what's still missing before deciding whether to search again.

Improvement:
Think of this like a senior editor reviewing a draft with a red pen.
A junior editor might mark everything as needing work.
A senior editor distinguishes between: "this kills the story" (critical),
"this weakens it" (important), and "this would be nice" (minor).

We only send reporters back out for critical gaps.
"""

import json
import anthropic
from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL_FAST


def detect_gaps(topic: str, research_so_far: list[dict], previous_gaps: list[dict] = None) -> list[dict]:
    """
    Read all research and return scored gaps.

    Each gap is a dict:
      {
        "description": "missing coverage of X",
        "severity":    3   # 3=critical, 2=important, 1=minor
      }

    Also compares against previous_gaps to assess progress.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    research_summary = "\n\n".join(
        f"Search: '{r['query']}'\nFindings: {r['content'][:500]}..."
        for r in research_so_far
        if r["success"]
    )

    # Tell the detector what gaps existed before so it can assess progress
    previous_text = ""
    if previous_gaps:
        previous_text = "\n\nGaps identified in the previous round:\n" + "\n".join(
            f"- [severity {g['severity']}] {g['description']}"
            for g in previous_gaps
        )
        previous_text += "\n\nFor each previous gap, assess whether the new research filled it before identifying remaining gaps."

    prompt = f"""You are evaluating research completeness on this topic:
Topic: "{topic}"

Research collected so far:
{research_summary}
{previous_text}

Identify gaps — important aspects not yet covered or covered too superficially.
Score each gap by severity:
  3 = critical — report is seriously incomplete without this
  2 = important — would meaningfully strengthen the report
  1 = minor — nice to have but not essential

Rules:
- Only list genuine gaps, not minor details unless truly important
- Be specific about what's missing
- Maximum 5 gaps total
- If research is comprehensive with no critical gaps, return empty list

Respond with ONLY a JSON array of objects. No explanation, no markdown.
Example:
[
  {{"description": "no data on costs", "severity": 3}},
  {{"description": "missing expert opinions", "severity": 2}}
]
Or [] if complete."""

    response = client.messages.create(
        model      = CLAUDE_MODEL_FAST,
        max_tokens = 300,
        messages   = [{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        gaps = json.loads(raw)
        if not isinstance(gaps, list):
            raise ValueError("Expected a list")

        # Validate structure
        validated = []
        for g in gaps:
            if isinstance(g, dict) and "description" in g and "severity" in g:
                validated.append({
                    "description": str(g["description"]),
                    "severity":    int(g["severity"])
                })

        print(f"  [GapDetector] Found {len(validated)} gaps:")
        for g in validated:
            print(f"  [GapDetector] [{g['severity']}] {g['description']}")

        return validated

    except (json.JSONDecodeError, ValueError) as e:
        print(f"  [GapDetector] Parse failed: {e}. Raw: {raw}")
        return []


def is_research_complete(gaps: list[dict]) -> bool:
    """
    Stop if no critical (severity 3) gaps remain.
    Minor and important gaps are acceptable — we don't chase perfection.
    """
    critical = [g for g in gaps if g["severity"] == 3]
    print(f"  [GapDetector] Critical gaps remaining: {len(critical)}")
    return len(critical) == 0