"""
Think of this like a managing editor running a newsroom.
They assign stories, read drafts, identify what's missing,
send reporters back out, and only call it done when the
critical stories are filed — or the deadline hits.

This file orchestrates the full research loop:
plan → search → detect gaps → plan again → repeat → report.
"""

from src.config       import DEPTH_PRESETS
from src.planner      import generate_queries
from src.searcher     import run_searches
from src.gap_detector import detect_gaps, is_research_complete
from src.reporter     import generate_report


class ResearchAgent:
    def __init__(self):
        print("[ResearchAgent] Ready.")

    def research(self, topic: str, depth: str = "fast") -> dict:
        """
        Run the full autonomous research loop on a topic.

        1. Plan initial search queries
        2. Run searches
        3. Detect gaps with severity scores
        4. If critical gaps remain and rounds left → plan new queries → go to 2
        5. Generate final report from all collected research
        """
        # Apply depth preset — controls how long the agent runs
        preset             = DEPTH_PRESETS.get(depth, DEPTH_PRESETS["fast"])
        max_rounds         = preset["max_rounds"]
        searches_per_round = preset["searches_per_round"]

        print(f"\n{'='*60}")
        print(f"[ResearchAgent] Topic: {topic}")
        print(f"[ResearchAgent] Depth: {depth} ({max_rounds} rounds, {searches_per_round} searches/round)")
        print(f"{'='*60}")

        all_research  = []   # every search result across all rounds
        all_queries   = []   # every query run — passed to planner to avoid repeats
        gaps          = []   # current round gaps (scored dicts)
        previous_gaps = []   # gaps from last round — passed to detector for progress awareness

        round_num = 1
        for round_num in range(1, max_rounds + 1):
            print(f"\n[ResearchAgent] Round {round_num}/{max_rounds}")

            # Step 1: plan — pass past queries so planner never repeats an angle
            print(f"[ResearchAgent] Planning searches...")
            queries = generate_queries(topic, gaps, round_num, past_queries=all_queries)
            print(f"[ResearchAgent] Queries: {queries}")
            all_queries.extend(queries)   # accumulate so future rounds know what ran

            # Step 2: run searches
            print(f"[ResearchAgent] Searching...")
            results = run_searches(queries)
            all_research.extend(results)

            # Step 3: detect gaps — pass previous_gaps so detector can assess progress
            print(f"[ResearchAgent] Detecting gaps...")
            previous_gaps = gaps          # hand current gaps to next round as history
            gaps          = detect_gaps(topic, all_research, previous_gaps=previous_gaps)

            # Step 4: decide whether to continue
            if is_research_complete(gaps):
                # No critical gaps remain — stop early, don't burn more API calls
                print(f"[ResearchAgent] No critical gaps remain. Stopping after round {round_num}.")
                break

            if round_num == max_rounds:
                print(f"[ResearchAgent] Max rounds reached. Writing report with what we have.")

        # Step 5: generate report from everything collected across all rounds
        print(f"\n[ResearchAgent] Generating report from {len(all_research)} searches...")
        result = generate_report(topic, all_research, depth)

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