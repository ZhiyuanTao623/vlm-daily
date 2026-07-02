"""Configuration for VLM Daily arXiv fetcher.

Edit the values below to tune what gets fetched. No code changes needed elsewhere.
"""
from pathlib import Path

# arXiv categories to search within.
CATEGORIES = ["cs.CV", "cs.CL", "cs.AI", "cs.LG", "cs.MM"]

# Only keep papers whose PRIMARY category is in this set. This filters out
# cross-listed papers whose real home field is something else entirely (e.g.
# astro-ph papers that merely mention "multimodal" data fusion).
ALLOWED_PRIMARY_CATEGORIES = ["cs.CV", "cs.CL", "cs.AI", "cs.LG", "cs.MM"]

# Keywords used both in the arXiv query and for a second relevance check.
# A paper is kept only if its title or abstract contains at least one of these.
# Kept intentionally specific to core VLM research (not bare "multimodal",
# which also matches EEG/clinical/audio/astro papers that merely fuse
# different data modalities but aren't vision-language models).
KEYWORDS = [
    "vision-language model",
    "vision-language models",
    "vision-language pretraining",
    "vision-language pre-training",
    "vision-language understanding",
    "vision-language reasoning",
    "large vision-language model",
    "visual language model",
    "VLM",
    "MLLM",
    "multimodal large language model",
    "multimodal LLM",
    "visual instruction tuning",
    "visual question answering",
    "image-text",
]

# A paper is dropped if its title or abstract contains any of these, even if
# it also matched a KEYWORDS term above. This excludes VLM-adjacent but
# non-"pure" application domains: robotics, autonomous driving, embodied
# action/navigation, etc.
EXCLUDE_KEYWORDS = [
    "autonomous driving",
    "self-driving",
    "vision-language-action",
    "vision language action",
    "VLA",
    "robot",
    "robotic",
    "navigation",
    "manipulation",
    "embodied",
    "world model",
]

# Maximum number of papers to show per day.
MAX_PAPERS = 20

# Only keep papers submitted within this many days (tolerates weekends / gaps).
# Kept a bit wider than 1 day because strict topic + top-50-school filtering
# is selective, so a short window can yield very few (or zero) papers.
DAYS_WINDOW = 4

# How many candidate results to request from the arXiv API per run. Stricter
# topic/school filtering drops more candidates, so this is set generously.
FETCH_BATCH = 300

# --- US top-50 CS school affiliation filter ---
# When True, each candidate paper's arXiv HTML page is fetched and the author /
# affiliation region is scanned for a US top-50 CS school. See notes below.
FILTER_BY_SCHOOL = True

# Policy for papers whose affiliation cannot be determined (no HTML version, or
# no recognizable institution text). "strict" drops them so that only papers
# with a clearly confirmed US top-50 affiliation are shown. "lenient" keeps
# them, which risks including non-US or non-top-50 papers whose affiliation
# text just didn't match our heuristics.
UNKNOWN_AFFILIATION_POLICY = "strict"

# Safety cap: at most this many candidates get an HTML fetch per run (bounds
# runtime). Iteration stops early once MAX_PAPERS keepers are collected.
SCHOOL_CHECK_CAP = 250

# Politeness delay (seconds) between arXiv HTML fetches.
HTML_FETCH_DELAY = 0.5

# Keywords that indicate the extracted region really contains affiliation info.
# Used by the "lenient" policy to decide a paper is determinable (and therefore
# droppable) rather than unknown.
ORG_KEYWORDS = [
    "university", "universit", "institute", "college", "laborator", "school of",
    "academy", "corporation", "research", "department", ".edu", ".ac.", "inc.",
]

# US top-50 CS schools. Each entry: display name + match patterns.
# Patterns that are UPPERCASE and short are matched as whole words (\bPAT\b);
# others are matched as case-insensitive substrings. Edit freely to taste.
TOP_SCHOOLS = [
    ("MIT", ["massachusetts institute of technology", "MIT"]),
    ("Stanford", ["stanford university", "stanford"]),
    ("Carnegie Mellon", ["carnegie mellon", "CMU"]),
    ("UC Berkeley", ["uc berkeley", "berkeley", "university of california, berkeley"]),
    ("UIUC", ["urbana-champaign", "urbana champaign", "UIUC"]),
    ("University of Washington", ["university of washington"]),
    ("Cornell", ["cornell university", "cornell tech", "cornell"]),
    ("Georgia Tech", ["georgia institute of technology", "georgia tech"]),
    ("Princeton", ["princeton university", "princeton"]),
    ("University of Michigan", ["university of michigan"]),
    ("UT Austin", ["university of texas at austin", "ut austin"]),
    ("Caltech", ["california institute of technology", "caltech"]),
    ("UCLA", ["ucla", "university of california, los angeles"]),
    ("UW-Madison", ["university of wisconsin"]),
    ("Columbia", ["columbia university"]),
    ("University of Maryland", ["university of maryland"]),
    ("Harvard", ["harvard university", "harvard"]),
    ("UC San Diego", ["uc san diego", "UCSD", "university of california, san diego"]),
    ("Yale", ["yale university"]),
    ("UPenn", ["university of pennsylvania", "upenn"]),
    ("Purdue", ["purdue university"]),
    ("Brown", ["brown university"]),
    ("Rice", ["rice university"]),
    ("UMass Amherst", ["university of massachusetts", "umass"]),
    ("USC", ["university of southern california", "USC"]),
    ("NYU", ["new york university", "NYU"]),
    ("Duke", ["duke university"]),
    ("Johns Hopkins", ["johns hopkins", "JHU"]),
    ("University of Chicago", ["university of chicago"]),
    ("Ohio State", ["ohio state university"]),
    ("Penn State", ["pennsylvania state university", "penn state"]),
    ("University of Minnesota", ["university of minnesota"]),
    ("UC Santa Barbara", ["uc santa barbara", "UCSB", "university of california, santa barbara"]),
    ("UNC Chapel Hill", ["university of north carolina", "chapel hill"]),
    ("Rutgers", ["rutgers university"]),
    ("UC Irvine", ["uc irvine", "UCI", "university of california, irvine"]),
    ("UC Davis", ["uc davis", "university of california, davis"]),
    ("Texas A&M", ["texas a&m"]),
    ("Northwestern", ["northwestern university"]),
    ("Virginia Tech", ["virginia tech", "virginia polytechnic"]),
    ("University of Virginia", ["university of virginia"]),
    ("Stony Brook", ["stony brook"]),
    ("Boston University", ["boston university"]),
    ("Arizona State", ["arizona state university"]),
    ("CU Boulder", ["university of colorado"]),
    ("NC State", ["north carolina state"]),
    ("University of Utah", ["university of utah"]),
    ("Dartmouth", ["dartmouth college"]),
    ("Vanderbilt", ["vanderbilt university"]),
    ("University of Rochester", ["university of rochester"]),
]

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
