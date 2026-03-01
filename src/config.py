import os
from dotenv import load_dotenv

load_dotenv()

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Haiku for planning and gap detection — structured reasoning tasks
CLAUDE_MODEL_FAST  = "claude-haiku-4-5-20251001"

# Sonnet for the final report — quality matters for the output the user reads
CLAUDE_MODEL_SMART = "claude-sonnet-4-6"

# Research loop controls
MAX_ROUNDS         = 5    # maximum research rounds before forcing a report
SEARCHES_PER_ROUND = 3    # how many search queries per round
GAP_THRESHOLD      = 3    # if fewer than this many gaps found, stop early

# Output
REPORTS_DIR = "reports"

# Depth presets — passed in from the UI
DEPTH_PRESETS = {
    "fast": {"max_rounds": 2, "searches_per_round": 3},
    "deep": {"max_rounds": 5, "searches_per_round": 5}
}
