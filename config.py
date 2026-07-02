"""Configuration for VLM Daily arXiv fetcher.

Edit the values below to tune what gets fetched. No code changes needed elsewhere.
"""
from pathlib import Path

# arXiv categories to search within.
CATEGORIES = ["cs.CV", "cs.CL", "cs.AI", "cs.LG", "cs.MM"]

# Keywords used both in the arXiv query and for a second relevance check.
# A paper is kept only if its title or abstract contains at least one of these.
KEYWORDS = [
    "vision-language",
    "vision language",
    "VLM",
    "multimodal",
    "MLLM",
    "visual question answering",
    "image-text",
    "vision-language model",
]

# Maximum number of papers to show per day.
MAX_PAPERS = 20

# Only keep papers submitted within this many days (tolerates weekends / gaps).
DAYS_WINDOW = 2

# How many candidate results to request from the arXiv API per run.
FETCH_BATCH = 100

# Site title shown on the generated pages.
SITE_TITLE = "VLM Daily"
SITE_SUBTITLE = "Daily Vision-Language Model papers from arXiv"

# --- Paths (usually no need to change) ---
ROOT = Path(__file__).resolve().parent
DOCS_DIR = ROOT / "docs"
DATA_DIR = ROOT / "data"
SEEN_IDS_FILE = DATA_DIR / "seen_ids.json"

# arXiv API endpoint
ARXIV_API = "http://export.arxiv.org/api/query"
