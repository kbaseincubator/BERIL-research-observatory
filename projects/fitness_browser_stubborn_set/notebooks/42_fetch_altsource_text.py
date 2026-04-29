"""
Fetch full-text or abstract from alternate sources for papers that have no
PMC version and no PubMed AbstractText. Tries in cascade:

  1. Europe PMC — full text or curated abstract
  2. OpenAlex   — abstract reconstructed from inverted index
  3. CrossRef   — abstract field via DOI (sometimes JATS-formatted)

Output:
  data/codex_summaries_altsource/text/<pmid>.txt   — best-quality text we found
  data/codex_summaries_altsource/source_index.tsv  — pmId, source, length
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
ALT_DIR = PROJECT_DATA / "codex_summaries_altsource"
TEXT_DIR = ALT_DIR / "text"
INDEX = ALT_DIR / "source_index.tsv"
TASKS = ALT_DIR / "tasks.jsonl"

NCBI_TOOL = "kbase-fb-stubborn"
NCBI_EMAIL = "psdehal@gmail.com"


def _strip_html(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


MAX_FULLTEXT_CHARS = 400_000  # codex hard input cap is ~1M; keep margin for prompt overhead


def europe_pmc(pmid: str) -> tuple[str, str]:
    """Returns (text, kind) where kind is 'epmc_fulltext' / 'epmc_abstract' / ''."""
    try:
        r = requests.get(
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
            params={"query": f"EXT_ID:{pmid} AND SRC:MED", "format": "json", "resultType": "core"},
            timeout=20,
        )
        if not r.ok:
            return ("", "")
        results = r.json().get("resultList", {}).get("result", [])
        if not results:
            return ("", "")
        rec = results[0]
        title = (rec.get("title") or "").rstrip(".")
        # Try full text first
        if rec.get("inEPMC") == "Y" or rec.get("hasFullText") == "Y":
            pmcid = rec.get("pmcid") or rec.get("PMCID")
            if pmcid:
                fr = requests.get(
                    f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML",
                    timeout=30,
                )
                if fr.ok and fr.text and len(fr.text) > 500:
                    body = _strip_html(fr.text)
                    if len(body) > MAX_FULLTEXT_CHARS:
                        # Too big — fall back to abstract instead of truncating mid-paper
                        ab = rec.get("abstractText")
                        if ab:
                            return (f"TITLE: {title}\n\nABSTRACT (Europe PMC, full text too long for codex):\n{_strip_html(ab)}", "epmc_abstract_oversized")
                    else:
                        return (f"TITLE: {title}\n\nFULL TEXT (Europe PMC):\n{body}", "epmc_fulltext")
        # Fall back to abstract
        ab = rec.get("abstractText")
        if ab:
            return (f"TITLE: {title}\n\nABSTRACT (Europe PMC):\n{_strip_html(ab)}", "epmc_abstract")
    except requests.RequestException:
        pass
    return ("", "")


def openalex(pmid: str) -> tuple[str, str]:
    try:
        r = requests.get(
            f"https://api.openalex.org/works/pmid:{pmid}",
            params={"mailto": NCBI_EMAIL},
            timeout=20,
        )
        if not r.ok:
            return ("", "")
        d = r.json()
        title = d.get("title") or ""
        inv = d.get("abstract_inverted_index")
        if not inv:
            return ("", "")
        # Reconstruct abstract from inverted index: word -> [positions]
        positions = []
        for word, idxs in inv.items():
            for i in idxs:
                positions.append((i, word))
        positions.sort()
        text = " ".join(w for _, w in positions)
        return (f"TITLE: {title}\n\nABSTRACT (OpenAlex):\n{text}", "openalex")
    except requests.RequestException:
        return ("", "")


def crossref(pmid: str) -> tuple[str, str]:
    """Need DOI first. Get DOI from OpenAlex (free), then query CrossRef."""
    try:
        r = requests.get(
            f"https://api.openalex.org/works/pmid:{pmid}",
            params={"mailto": NCBI_EMAIL},
            timeout=15,
        )
        if not r.ok:
            return ("", "")
        doi = (r.json().get("doi") or "").replace("https://doi.org/", "")
        if not doi:
            return ("", "")
        cr = requests.get(
            f"https://api.crossref.org/works/{doi}",
            headers={"User-Agent": f"kbase-fb (mailto:{NCBI_EMAIL})"},
            timeout=20,
        )
        if not cr.ok:
            return ("", "")
        msg = cr.json().get("message", {})
        title = ""
        if msg.get("title"):
            title = msg["title"][0] if isinstance(msg["title"], list) else msg["title"]
        ab = msg.get("abstract")
        if not ab:
            return ("", "")
        return (f"TITLE: {title}\n\nABSTRACT (CrossRef):\n{_strip_html(ab)}", "crossref")
    except requests.RequestException:
        return ("", "")


def fetch_one(pmid: str) -> tuple[str, str]:
    """Cascade through sources; return first hit."""
    for src in (europe_pmc, openalex, crossref):
        text, kind = src(pmid)
        if text and len(text) > 200:
            return (text, kind)
    return ("", "")


def main() -> None:
    TEXT_DIR.mkdir(parents=True, exist_ok=True)

    todo = []
    with open(TASKS) as fh:
        for line in fh:
            t = json.loads(line)
            pmid = t["pmId"]
            if pmid in (None, "None"):
                continue
            if (TEXT_DIR / f"{pmid}.txt").exists():
                continue
            todo.append(pmid)
    print(f"Papers to fetch from alt sources: {len(todo)}", file=sys.stderr)

    by_source = {}
    written = 0
    for i, pmid in enumerate(todo, 1):
        text, kind = fetch_one(pmid)
        if text:
            (TEXT_DIR / f"{pmid}.txt").write_text(text)
            by_source[kind] = by_source.get(kind, 0) + 1
            written += 1
        if i % 5 == 0:
            print(f"  ...{i}/{len(todo)} (got {written}, sources: {by_source})", file=sys.stderr)
        time.sleep(0.3)  # politeness

    # Index
    with open(INDEX, "w") as fh:
        fh.write("pmId\tsource\tlength\n")
        with open(TASKS) as tfh:
            for line in tfh:
                t = json.loads(line)
                pmid = t["pmId"]
                if pmid in (None, "None"):
                    continue
                txt_file = TEXT_DIR / f"{pmid}.txt"
                if txt_file.exists():
                    body = txt_file.read_text()
                    # Source is the line after first "TITLE: ..."
                    m = re.search(r"\((Europe PMC|OpenAlex|CrossRef)\)", body)
                    src = m.group(1) if m else "?"
                    fh.write(f"{pmid}\t{src}\t{len(body)}\n")
                else:
                    fh.write(f"{pmid}\tnone\t0\n")

    print(f"\nFetched: {written}/{len(todo)}", file=sys.stderr)
    print(f"By source: {by_source}", file=sys.stderr)


if __name__ == "__main__":
    main()
