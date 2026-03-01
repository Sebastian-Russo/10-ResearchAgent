# 10-ResearchAgent

## What's New Here

**The Anthropic web search tool** — Claude can call a built-in web search tool natively through the API. Instead of us scraping URLs ourselves, we give Claude the ability to search and read pages as part of its reasoning loop. This is different from every previous project — the LLM is now deciding what to search for, not us.

**Gap detection** — after each round of research, the agent reads what it has found and asks "what important questions about this topic are still unanswered?" Those gaps become the next round of searches. This is what makes it genuinely autonomous.

**Multi-round planning** — the agent doesn't just search once. It plans, searches, evaluates gaps, plans again, searches again, until either the gaps are filled or it hits the max rounds limit.

### The Loop
topic given
    ↓
[PLAN]    generate initial search queries
    ↓
[SEARCH]  run searches, scrape results
    ↓
[EVALUATE] what gaps remain?
    ↓
gaps exist + rounds left → back to PLAN with new queries
    ↓
no gaps or max rounds hit
    ↓
[REPORT]  synthesize everything into structured report

### Project Structure

```
10-ResearchAgent/
├── src/
│   ├── config.py
│   ├── planner.py        ← generate search queries from topic + gaps
│   ├── searcher.py       ← run web searches via Anthropic tool
│   ├── gap_detector.py   ← identify what's still missing
│   ├── reporter.py       ← synthesize final report
│   ├── research_agent.py ← orchestrates the full loop
│   └── __init__.py
├── static/
│   └── index.html
├── reports/              ← saved markdown reports
├── app.py
├── requirements.txt
└── .gitignore
```


Start with what the user does and follow it all the way through.

## You type a topic and hit Start Research

The browser sends the topic and depth setting to **/research** in **app.py**. Flask hands it to **ResearchAgent.research()**. From here the user just waits — everything that happens next is autonomous.

### Round 1 — broad exploration

The agent calls **planner.py** first. Since it's round 1 with no gaps yet, the planner asks Haiku to think about the topic and generate 3-5 broad search queries covering different angles. For "nuclear fusion energy" it might return: "current state nuclear fusion 2025", "nuclear fusion energy companies progress", "ITER fusion reactor timeline".

Those queries go to **searcher.py**. For each query, it calls the Anthropic API with the web search tool enabled. This is different from every previous project — Claude itself decides what pages to visit, reads them, and returns a written summary of what it found. We don't scrape anything directly. We just get back a paragraph of synthesized findings per query.

All results accumulate in **all_research** — a running list of every query and its findings across all rounds.

### Gap detection — should we keep going?

**gap_detector.py** reads everything in **all_research** so far and asks Haiku: "given all this, what important aspects of the topic are still missing?" It returns a list like: "no information on fusion energy costs", "missing coverage of private sector investment", "nothing about timeline to commercial viability".

Then **is_research_complete()** checks the count. If fewer than 3 gaps remain, research is considered complete and the loop exits early. If 3 or more gaps exist and rounds remain, the loop continues.

### Round 2+ — targeted gap filling

The planner gets called again, but this time it receives the gap list. Instead of broad queries it generates targeted ones aimed specifically at what's missing — "nuclear fusion energy cost per kilowatt", "private fusion startups Commonwealth Fusion TAE Technologies", "when will fusion be commercially viable".

The searcher runs those, results go into **all_research**, gap detector runs again. This repeats until either the gaps drop below the threshold or the max rounds limit is hit.

### Report generation

Once the loop exits, **reporter.py** takes the entire **all_research** list — every finding from every round — and sends it to Claude Sonnet with a structured prompt: write a professional markdown report with an executive summary, clear section headers, specific facts from the research, and a key takeaways section.

Sonnet synthesizes everything into a coherent document. The report gets saved to disk with a timestamp filename and returned to the browser simultaneously.

### What makes this genuinely agentic

Every previous project had a fixed pipeline — inputs went in, outputs came out, same steps every time. This agent makes decisions mid-run. It decides how many rounds to run based on what it finds. It decides what to search for in round 2 based on what was missing in round 1. It decides when enough is enough. The path through the code is different every time depending on the topic and what the searches return. Sonnet 4.6


--------------------------------------------------------------------------------------------

## Search Adjustments

**More searches per round** — just increase SEARCHES_PER_ROUND in config. Easy but costs more tokens.
**More rounds** — increase MAX_ROUNDS. The genocide topic hit the ceiling at 2, bumping to 3-4 would let it keep filling gaps.
**Lower the gap threshold** — currently stops when fewer than 3 gaps remain. Dropping to 1 means it keeps searching until it's nearly complete.
**Smarter gap detection** — right now it finds 5 gaps every round even when research is improving. We could change the prompt to score gap severity and only continue if high-severity gaps remain.
**Cross-referencing** — after all searches complete, have Claude identify where sources agree vs conflict before writing the report. Adds a verification layer.
**Source diversity check** — tell the planner to explicitly vary search angles each round so it doesn't circle back to similar queries.

Looking at your run, the most obvious issue is that gaps never dropped below 5 across both rounds — meaning the gap detector isn't distinguishing between "critical missing information" and "would be nice to have." The planner was generating good targeted queries but the evaluator kept finding new gaps instead of acknowledging progress.

## Adjustments to be made

1. **Smarter gap detection** — severity scoring
Instead of just counting gaps, score each one 1-3:

3 = critical, report is incomplete without this
2 = important, would strengthen the report
1 = nice to have, minor detail

Only continue searching if any score-3 gaps remain. This stops the agent from chasing minor gaps forever and explains why your genocide topic kept hitting 5 gaps — some of those were genuinely critical, others were just "more detail would be nice."

2. **Progress awareness in the gap detector**
Right now the gap detector reads all research but doesn't know what round it's on or how much progress was made since last round. We should tell it: "last round you found these 5 gaps, here's the new research, which gaps were actually filled?" That way it evaluates improvement not just remaining gaps, which is a much more honest stopping condition.
These two changes work together — severity tells you what matters, progress awareness tells you if you're actually getting closer.
One more I'd add:

3. **Deduplicate queries across rounds**
Your round 2 queries were good but slightly overlapped with round 1. The planner should receive the full list of queries already run so it never searches the same angle twice. One line change in **research_agent.py** — pass **all_research** queries to the planner so it knows what's already been covered.

