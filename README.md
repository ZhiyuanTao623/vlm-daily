# VLM Daily

Automatically fetches recent **Vision-Language Model (VLM) papers** from [arXiv](https://arxiv.org/) every day, generating a title, authors, original abstract, and links for each, then publishes them as a public web page.

🌐 **Live site**: https://zhiyuantao623.github.io/vlm-daily/

## How it works

- **GitHub Actions** runs `vlm_daily.py` in the cloud every day at 01:00 UTC — your computer does not need to be on.
- The script queries arXiv, filters recent VLM-related papers, dedupes them, and renders HTML into `docs/`.
- The changes are committed back to the repo, and **GitHub Pages** serves the site from the `/docs` folder on the `main` branch.
- The blurb is simply the original arXiv abstract, so **no API key and no cost** are required.

## Run locally

No dependencies to install (pure Python standard library, Python 3.9+):

```bash
python vlm_daily.py
```

Then open `docs/index.html` in your browser.

## Configuration

Edit [`config.py`](config.py):

| Setting | Description |
| --- | --- |
| `CATEGORIES` | arXiv categories to search (e.g. `cs.CV`, `cs.CL`) |
| `ALLOWED_PRIMARY_CATEGORIES` | Only keep papers whose *primary* category is in this set (drops cross-listed papers from unrelated fields, e.g. astro-ph) |
| `KEYWORDS` | Keywords for core VLM research (used both for the query and a second relevance check). Deliberately specific — bare terms like `"multimodal"` are excluded because they also match EEG/clinical/audio/astro papers that aren't vision-language models |
| `EXCLUDE_KEYWORDS` | Drops a paper even if it matched `KEYWORDS`, e.g. robotics/autonomous-driving/embodied-action terms, to keep results to "pure" VLM research |
| `MAX_PAPERS` | Max papers to show per day (default 20) |
| `DAYS_WINDOW` | Keep only papers submitted within this many days (default 4 — wider than 1 day because strict topic + school filtering is selective) |
| `FETCH_BATCH` | Number of candidate results requested from arXiv per run |
| `FILTER_BY_SCHOOL` | Keep only papers with a **US top-50 CS school** author (default `True`) |
| `UNKNOWN_AFFILIATION_POLICY` | When affiliation is undeterminable: `"strict"` (drop, default — only confirmed top-50 papers are shown) or `"lenient"` (keep) |
| `TOP_SCHOOLS` | The US top-50 CS school list and match patterns — edit freely |
| `SCHOOL_CHECK_CAP` | Max candidates fetched/checked per run (bounds runtime) |

With strict topic and school filtering, expect roughly **5-15 papers/day**
rather than a fixed 20 — quality/precision is prioritized over volume.

### How the school filter works

arXiv API metadata almost never includes author affiliations, and external
databases (OpenAlex / Semantic Scholar) lag behind the newest papers. So for
each candidate this tool fetches the paper's **arXiv HTML version**
(`https://arxiv.org/html/<id>`, available as soon as a paper is posted),
extracts the author/affiliation region (between the title and the Abstract),
and matches it against the `TOP_SCHOOLS` list. Matched papers show a green
school badge on their card.

This is heuristic matching, not 100% accurate: papers without an HTML version
or with unusual affiliation formatting may be missed. Under the default
`strict` policy such "undeterminable" papers are dropped, so only papers with
a clearly confirmed US top-50 affiliation are shown.

To change the schedule, edit the `cron` expression (UTC) in
[`.github/workflows/daily.yml`](.github/workflows/daily.yml).

## Enable GitHub Pages (one-time)

In the repo's **Settings → Pages**, set Source to **Deploy from a branch**,
choose the `main` branch and the `/docs` folder, and save. The live site is
available a minute or two later.

## Files

- `vlm_daily.py` — main script: fetch → dedupe → render HTML.
- `config.py` — tunable settings.
- `docs/` — generated site (GitHub Pages root).
- `data/seen_ids.json` — IDs of already-shown papers, used for cross-day dedupe (committed back to the repo).
- `.github/workflows/daily.yml` — the daily GitHub Actions workflow.
