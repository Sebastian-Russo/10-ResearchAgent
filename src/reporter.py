"""
Think of this like a senior analyst who has been handed
a stack of research notes from junior researchers.
They don't go find more information — their job is to take
everything on the table and write the definitive report.

This file takes all collected research and synthesizes
it into a structured markdown report with clear sections.
"""

import os
import re
from datetime import datetime
import anthropic
from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL_SMART, REPORTS_DIR


def generate_report(topic: str, research: list[dict], depth: str) -> dict:
    """
    Synthesize all research into a structured markdown report.

    Returns:
      - report:    full markdown text
      - filepath:  where the report was saved on disk
      - sources:   list of queries that contributed
      - word_count: approximate length
    """
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        # Build the full evidence block from all successful searches
        evidence = "\n\n".join(
            f"### Research from: '{r['query']}'\n{r['content']}"
            for r in research
            if r["success"]
        )

        prompt = f"""You are a professional research analyst writing a comprehensive report.

Topic: "{topic}"
Research depth: {depth}

All research collected:
{evidence}

Write a well-structured markdown report covering this topic thoroughly.

Requirements:
- Start with an executive summary (2-3 sentences)
- Use clear ## section headers for each major angle
- Include specific facts, numbers, and names from the research
- Note where evidence is thin or conflicting
- End with a ## Key Takeaways section (5 bullet points)
- Do not invent information not present in the research

Write the full report now:"""

        response = client.messages.create(
            model      = CLAUDE_MODEL_SMART,
            max_tokens = 3000,
            messages   = [{"role": "user", "content": prompt}]
        )

        report_text = response.content[0].text.strip()

        # Save to disk
        os.makedirs(REPORTS_DIR, exist_ok=True)
        timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic  = re.sub(r'[^a-z0-9]+', '_', topic.lower())[:40]
        filename    = f"{timestamp}_{safe_topic}.md"
        filepath    = os.path.join(REPORTS_DIR, filename)

        with open(filepath, "w") as f:
            f.write(f"# {topic}\n\n")
            f.write(report_text)

        sources = [r["query"] for r in research if r["success"]]
        word_count = len(report_text.split())

        return {
            "report":     report_text,
            "filepath":   filepath,
            "sources":    sources,
            "word_count": word_count
        }
    except Exception as e:
        print(f"[Reporter] Error generating report: {e}")
        # Return a fallback report when API fails
        fallback_report = f"# {topic}\n\nError: Unable to generate report due to API issues. Raw research data:\n\n"
        for r in research:
            if r["success"]:
                fallback_report += f"## {r['query']}\n{r['content']}\n\n"

        # Still save the fallback
        os.makedirs(REPORTS_DIR, exist_ok=True)
        timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic  = re.sub(r'[^a-z0-9]+', '_', topic.lower())[:40]
        filename    = f"{timestamp}_{safe_topic}_fallback.md"
        filepath    = os.path.join(REPORTS_DIR, filename)

        with open(filepath, "w") as f:
            f.write(fallback_report)

        return {
            "report":     fallback_report,
            "filepath":   filepath,
            "sources":    [r["query"] for r in research if r["success"]],
            "word_count": len(fallback_report.split())
        }

    # This should never be reached due to returns above, but silences IDE warnings
    return {
        "report": "",
        "filepath": "",
        "sources": [],
        "word_count": 0
    }
