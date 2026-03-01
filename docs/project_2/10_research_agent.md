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