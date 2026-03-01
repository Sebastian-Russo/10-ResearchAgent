"""
Think of this like a managing editor running a newsroom.
They assign stories, read drafts, identify what's missing,
send reporters back out, and only call it done when the
story is ready to publish — or the deadline hits.

This file orchestrates the full research loop:
plan → search → detect gaps → plan again → repeat → report.
It's the equivalent of rag_pipeline.py and game_engine.py
from previous projects — the conductor that coordinates everything.
"""

from src.config     import DEPTH_PRESETS, MAX_ROUNDS, SEARCHES_PER_ROUND
from src.planner    import generate_queries
from src.searcher   import run_searches
from src.gap_detector import detect_gaps, is_research_complete
from src.reporter   import generate_report


class ResearchAgent:
    def __init__(self):
        print("[ResearchAgent] Ready.")

    def research(self, topic: str, depth: str = "fast") -> dict:
        """
        Run the full autonomous research loop on a topic.

        1. Plan initial search queries
        2. Run searches
        3. Detect gaps
        4. If gaps remain and rounds left → plan new queries targeting gaps → go to 2
        5. Generate final report from all collected research
        """
        # Apply depth preset — overrides defaults from config
        preset = DEPTH_PRESETS.get(depth, DEPTH_PRESETS["fast"])
        max_rounds         = preset["max_rounds"]
        searches_per_round = preset["searches_per_round"]

        print(f"\n{'='*60}")
        print(f"[ResearchAgent] Topic: {topic}")
        print(f"[ResearchAgent] Depth: {depth} ({max_rounds} rounds, {searches_per_round} searches/round)")
        print(f"{'='*60}")

        all_research = []   # accumulates every search result across all rounds
        gaps         = []   # gaps detected after each round

        for round_num in range(1, max_rounds + 1):
            print(f"\n[ResearchAgent] Round {round_num}/{max_rounds}")

            # Step 1: plan queries for this round
            print(f"[ResearchAgent] Planning searches...")
            queries = generate_queries(topic, gaps, round_num)
            print(f"[ResearchAgent] Queries: {queries}")

            # Step 2: run searches
            print(f"[ResearchAgent] Searching...")
            results = run_searches(queries)
            all_research.extend(results)

            # Step 3: detect gaps
            print(f"[ResearchAgent] Detecting gaps...")
            gaps = detect_gaps(topic, all_research)

            # Step 4: decide whether to continue
            if is_research_complete(gaps):
                print(f"[ResearchAgent] Research complete after round {round_num}.")
                break

            if round_num == max_rounds:
                print(f"[ResearchAgent] Max rounds reached. Writing report with what we have.")

        # Step 5: generate report
        print(f"\n[ResearchAgent] Generating report from {len(all_research)} searches...")
        result = generate_report(topic, all_research, depth)

        # Validate result is a dictionary with expected keys
        if not isinstance(result, dict):
            print(f"[ResearchAgent] Error: generate_report returned invalid result: {result}")
            result = {
                "report": f"Error: Unable to generate report for topic '{topic}'",
                "filepath": "",
                "sources": [],
                "word_count": 0
            }

        # Ensure all expected keys exist
        result.setdefault("report", "")
        result.setdefault("filepath", "")
        result.setdefault("sources", [])
        result.setdefault("word_count", 0)

        print(f"[ResearchAgent] Done. {result['word_count']} words. Saved to {result['filepath']}")

        return {
            "topic":        topic,
            "depth":        depth,
            "rounds_run":   round_num,
            "searches_run": len(all_research),
            "report":       result["report"],
            "filepath":     result["filepath"],
            "sources":      result["sources"],
            "word_count":   result["word_count"]
        }
