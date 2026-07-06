#!/usr/bin/env python3
"""VLM Daily -- fetch recent Vision-Language Model papers from arXiv and render
them as static HTML pages for GitHub Pages.

Pure standard library: no third-party dependencies.

Run:  python vlm_daily.py
"""
from __future__ import annotations

import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

import config

ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"


# --------------------------------------------------------------------------- #
# Fetching & parsing
# --------------------------------------------------------------------------- #
def build_query() -> str:
    """Build the arXiv search_query string from config."""
    cats = " OR ".join(f"cat:{c}" for c in config.CATEGORIES)
    # Quote multi-word keywords so the API treats them as phrases.
    kw_terms = []
    for kw in config.KEYWORDS:
        if " " in kw or "-" in kw:
            kw_terms.append(f'abs:"{kw}"')
        else:
            kw_terms.append(f"abs:{kw}")
    kws = " OR ".join(kw_terms)
    return f"({cats}) AND ({kws})"


def fetch_feed(retries: int = 5) -> str:
    """Query the arXiv API and return the raw Atom XML string."""
    params = {
        "search_query": build_query(),
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": str(config.FETCH_BATCH),
    }
    url = f"{config.ARXIV_API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "VLM-Daily/1.0 (+github pages)"})

    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                return resp.read().decode("utf-8")
        except Exception as err:  # network hiccups / rate limits
            last_err = err
            print(f"  fetch attempt {attempt} failed: {err}", file=sys.stderr)
            if attempt < retries:
                time.sleep(5 * attempt)
    raise RuntimeError(f"Failed to fetch arXiv feed after {retries} attempts: {last_err}")


def parse_entries(xml_text: str) -> list[dict]:
    """Parse Atom XML into a list of paper dicts."""
    root = ET.fromstring(xml_text)
    papers: list[dict] = []
    for entry in root.findall(f"{ATOM}entry"):
        raw_id = _text(entry.find(f"{ATOM}id"))  # e.g. http://arxiv.org/abs/2401.01234v1
        arxiv_id = raw_id.rsplit("/abs/", 1)[-1] if "/abs/" in raw_id else raw_id
        base_id = arxiv_id.split("v")[0]  # strip version for dedupe

        title = " ".join(_text(entry.find(f"{ATOM}title")).split())
        summary = " ".join(_text(entry.find(f"{ATOM}summary")).split())
        published = _text(entry.find(f"{ATOM}published"))
        updated = _text(entry.find(f"{ATOM}updated"))

        authors = [
            _text(a.find(f"{ATOM}name"))
            for a in entry.findall(f"{ATOM}author")
        ]

        primary = entry.find(f"{ARXIV_NS}primary_category")
        category = primary.get("term") if primary is not None else ""

        abs_link = raw_id
        pdf_link = ""
        for link in entry.findall(f"{ATOM}link"):
            if link.get("title") == "pdf":
                pdf_link = link.get("href", "")
            elif link.get("rel") == "alternate":
                abs_link = link.get("href", abs_link)
        if not pdf_link and base_id:
            pdf_link = f"https://arxiv.org/pdf/{arxiv_id}"

        papers.append(
            {
                "id": base_id,
                "arxiv_id": arxiv_id,
                "title": title,
                "summary": summary,
                "authors": authors,
                "published": published,
                "updated": updated,
                "category": category,
                "abs_link": abs_link,
                "pdf_link": pdf_link,
            }
        )
    return papers


def _text(elem) -> str:
    return elem.text.strip() if elem is not None and elem.text else ""


# --------------------------------------------------------------------------- #
# Filtering
# --------------------------------------------------------------------------- #
def _parse_dt(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def is_recent(paper: dict) -> bool:
    cutoff = datetime.now(timezone.utc) - timedelta(days=config.DAYS_WINDOW)
    dt = _parse_dt(paper.get("published", "")) or _parse_dt(paper.get("updated", ""))
    if dt is None:
        return False
    return dt >= cutoff


def is_relevant(paper: dict) -> bool:
    haystack = (paper["title"] + " " + paper["summary"]).lower()
    return any(kw.lower() in haystack for kw in config.KEYWORDS)


def is_excluded(paper: dict) -> bool:
    """True if the paper matches an EXCLUDE_KEYWORDS term (e.g. robotics,
    autonomous driving, embodied action) and should be dropped even though it
    matched a VLM keyword."""
    text = paper["title"] + " " + paper["summary"]
    low = text.lower()
    for term in config.EXCLUDE_KEYWORDS:
        if term.isupper() and len(term) <= 5:  # abbreviation -> whole word
            if re.search(r"\b" + re.escape(term) + r"\b", text):
                return True
        elif term.lower() in low:
            return True
    return False


def is_allowed_category(paper: dict) -> bool:
    return paper.get("category", "") in config.ALLOWED_PRIMARY_CATEGORIES


# --------------------------------------------------------------------------- #
# Affiliation (US top-50 CS school) filtering
# --------------------------------------------------------------------------- #
# Marker like: "arXiv:2607.00726v1 [cs.CV] 01 Jul 2026"
_ARXIV_MARKER = re.compile(
    r"arXiv:\d{4}\.\d{4,5}(?:v\d+)?\s*\[[^\]]+\]\s*\d{1,2}\s+\w+\s+\d{4}"
)


def _extract_region(html_text: str) -> str:
    """From an arXiv HTML page, return the author/affiliation text region
    (between the arXiv identifier line and the Abstract heading)."""
    html_text = re.sub(r"<script.*?</script>", " ", html_text, flags=re.S | re.I)
    html_text = re.sub(r"<style.*?</style>", " ", html_text, flags=re.S | re.I)
    text = re.sub("<[^>]+>", " ", html_text)
    text = re.sub(r"\s+", " ", text).strip()

    m = _ARXIV_MARKER.search(text)
    rest = text[m.end():] if m else ""
    if not rest:
        return ""
    ab = re.search(r"\bAbstract\b", rest)
    region = rest[: ab.start()] if ab else rest[:1500]
    return region.strip()


def fetch_affiliation_region(arxiv_id: str) -> str | None:
    """Fetch the arXiv HTML version and extract the affiliation region.
    Returns None if no HTML version is available."""
    candidates = [arxiv_id]
    base = arxiv_id.split("v")[0]
    if base != arxiv_id:
        candidates.append(base)
    for aid in candidates:
        url = f"https://arxiv.org/html/{aid}"
        req = urllib.request.Request(url, headers={"User-Agent": "VLM-Daily/1.0 (+github pages)"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                html_text = resp.read().decode("utf-8", "ignore")
        except Exception:
            continue
        region = _extract_region(html_text)
        if region:
            return region
    return None


def match_schools(region: str) -> list[str]:
    """Return the list of US top-50 CS schools detected in the region."""
    if not region:
        return []
    low = region.lower()
    matched: list[str] = []
    for name, patterns in config.TOP_SCHOOLS:
        for pat in patterns:
            if pat.isupper() and len(pat) <= 5:  # abbreviation -> whole word
                if re.search(r"\b" + re.escape(pat) + r"\b", region):
                    matched.append(name)
                    break
            elif pat.lower() in low:  # full name -> substring
                matched.append(name)
                break
    return matched


def region_is_determinable(region: str | None) -> bool:
    """True if the region plausibly contains real affiliation text (so a
    no-match result means 'not a top-50 school' rather than 'unknown')."""
    if not region or len(region) < 15:
        return False
    low = region.lower()
    return any(kw in low for kw in config.ORG_KEYWORDS)


def load_seen() -> set[str]:
    if config.SEEN_IDS_FILE.exists():
        try:
            return set(json.loads(config.SEEN_IDS_FILE.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            return set()
    return set()


def save_seen(seen: set[str]) -> None:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    config.SEEN_IDS_FILE.write_text(
        json.dumps(sorted(seen), indent=0, ensure_ascii=False), encoding="utf-8"
    )


# --------------------------------------------------------------------------- #
# HTML rendering
# --------------------------------------------------------------------------- #
def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def render_paper_card(paper: dict) -> str:
    authors = ", ".join(paper["authors"])
    if len(paper["authors"]) > 8:
        authors = ", ".join(paper["authors"][:8]) + " et al."
    date = (paper.get("published", "")[:10]) or ""
    cat = paper.get("category", "")
    schools = paper.get("schools") or []
    school_badges = "".join(
        f'<span class="school">{_esc(s)}</span>' for s in schools
    )
    return f"""      <article class="card">
        <h2><a href="{_esc(paper['abs_link'])}" target="_blank" rel="noopener">{_esc(paper['title'])}</a></h2>
        <div class="meta">
          <span class="date">{_esc(date)}</span>
          {f'<span class="cat">{_esc(cat)}</span>' if cat else ''}
          {school_badges}
          <span class="arxiv-id">arXiv:{_esc(paper['arxiv_id'])}</span>
        </div>
        <p class="authors">{_esc(authors)}</p>
        <p class="abstract">{_esc(paper['summary'])}</p>
        <div class="links">
          <a href="{_esc(paper['abs_link'])}" target="_blank" rel="noopener">[abs]</a>
          <a href="{_esc(paper['pdf_link'])}" target="_blank" rel="noopener">[pdf]</a>
        </div>
      </article>"""


def render_daily_page(date_str: str, papers: list[dict]) -> str:
    cards = "\n".join(render_paper_card(p) for p in papers)
    count = len(papers)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_esc(config.SITE_TITLE)} — {_esc(date_str)}</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <header class="site-header">
    <h1><a href="index.html">{_esc(config.SITE_TITLE)}</a></h1>
    <p class="subtitle">{_esc(config.SITE_SUBTITLE)}</p>
  </header>
  <main>
    <div class="day-head">
      <h2 class="day-title">{_esc(date_str)}</h2>
      <p class="count">{count} paper{'s' if count != 1 else ''}</p>
      <p><a href="index.html">&larr; All days</a></p>
    </div>
{cards if cards else '    <p class="empty">No new papers found for this day.</p>'}
  </main>
  <footer>
    <p>Generated {_esc(datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'))} ·
       Source: <a href="https://arxiv.org/" target="_blank" rel="noopener">arXiv</a></p>
  </footer>
</body>
</html>
"""


def render_index(day_files: list[str]) -> str:
    """day_files: sorted (desc) list of 'YYYY-MM-DD.html' names."""
    items = []
    for fname in day_files:
        date_str = fname[:-5]  # strip .html
        items.append(f'      <li><a href="{_esc(fname)}">{_esc(date_str)}</a></li>')
    listing = "\n".join(items) if items else '      <li class="empty">No days yet.</li>'
    latest_link = ""
    if day_files:
        latest_link = f'<p class="latest"><a href="{_esc(day_files[0])}">→ View latest ({_esc(day_files[0][:-5])})</a></p>'
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_esc(config.SITE_TITLE)}</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <header class="site-header">
    <h1>{_esc(config.SITE_TITLE)}</h1>
    <p class="subtitle">{_esc(config.SITE_SUBTITLE)}</p>
  </header>
  <main>
    {latest_link}
    <h2>Archive</h2>
    <ul class="day-list">
{listing}
    </ul>
  </main>
  <footer>
    <p>Auto-updated daily via GitHub Actions ·
       Source: <a href="https://arxiv.org/" target="_blank" rel="noopener">arXiv</a></p>
  </footer>
</body>
</html>
"""


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> int:
    config.DOCS_DIR.mkdir(parents=True, exist_ok=True)
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("Fetching arXiv feed ...")
    xml_text = fetch_feed()
    papers = parse_entries(xml_text)
    print(f"  parsed {len(papers)} candidate entries")

    seen = load_seen()
    selected: list[dict] = []
    checked = 0
    dropped_non_us = 0
    for p in papers:
        if len(selected) >= config.MAX_PAPERS:
            break
        if p["id"] in seen:
            continue
        if not is_recent(p):
            continue
        if not is_allowed_category(p):
            continue
        if not is_relevant(p):
            continue
        if is_excluded(p):
            continue

        if config.FILTER_BY_SCHOOL:
            if checked >= config.SCHOOL_CHECK_CAP:
                print("  reached SCHOOL_CHECK_CAP; stopping affiliation checks")
                break
            checked += 1
            region = fetch_affiliation_region(p["arxiv_id"])
            time.sleep(config.HTML_FETCH_DELAY)
            schools = match_schools(region)
            if schools:
                p["schools"] = schools
            elif region_is_determinable(region):
                dropped_non_us += 1  # has affiliations, none top-50 -> drop
                continue
            elif config.UNKNOWN_AFFILIATION_POLICY == "strict":
                continue
            else:
                p["schools"] = []  # unknown affiliation, kept (lenient)

        selected.append(p)

    if config.FILTER_BY_SCHOOL:
        print(
            f"  {len(selected)} papers kept "
            f"(checked {checked}, dropped {dropped_non_us} clearly non-top-50)"
        )
    else:
        print(f"  {len(selected)} new relevant papers after filtering/dedupe")

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    daily_path = config.DOCS_DIR / f"{date_str}.html"

    if not selected and daily_path.exists():
        print("  nothing new; leaving existing page untouched")
    else:
        daily_path.write_text(render_daily_page(date_str, selected), encoding="utf-8")
        print(f"  wrote {daily_path}")

    # Update seen set with newly shown papers.
    for p in selected:
        seen.add(p["id"])
    save_seen(seen)

    # Rebuild index from all day pages present in docs/.
    day_files = sorted(
        (f.name for f in config.DOCS_DIR.glob("*.html") if f.name != "index.html"),
        reverse=True,
    )
    (config.DOCS_DIR / "index.html").write_text(render_index(day_files), encoding="utf-8")
    print(f"  updated index with {len(day_files)} day page(s)")

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
