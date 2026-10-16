"""Pull the Business/Competition text from each company's latest 10-K for competitor cards.

For every ticker given, finds the latest 10-K accepted before the decision time,
downloads the primary document, strips HTML and saves:
  - the "Competition" passage(s) inside Item 1, with character offsets
  - the opening of Item 1 (business model / customers)
Also runs SEC full-text search for other 10-Ks that mention the company name
(reverse mentions), restricted to filings before the decision time.

Usage: python scripts/extract_competition_v1.py --cache DIR --out DIR TICKER [TICKER ...]
"""

from __future__ import annotations

import argparse
import gzip
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import yaml  # noqa: E402

from pit_rotation import inflection as inf  # noqa: E402
from pit_rotation import universe as uni  # noqa: E402
from pit_rotation.fetch import SEC_USER_AGENT, CachedFetcher  # noqa: E402

ARCHIVE = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}"
EFTS = "https://efts.sec.gov/LATEST/search-index?q={q}&forms=10-K&dateRange=custom&startdt={s}&enddt={e}"
STOP_HEADINGS = re.compile(
    r"\n\s*(Intellectual Property|Patents|Proprietary Rights|Government Regulation|Regulation|Employees|"
    r"Human Capital|Research and Development|Seasonality|Backlog|Environmental|Available Information|"
    r"Properties|Item\s+1A|ITEM\s+1A|Manufacturing|Sales and Marketing|Suppliers|Raw Materials|Customers)\b[^\n]{0,60}\n"
)


def html_to_text(raw: bytes) -> str:
    s = raw.decode("utf-8", errors="ignore")
    s = re.sub(r"(?is)<(script|style).*?</\1>", " ", s)
    s = re.sub(r"(?is)<ix:header>.*?</ix:header>", " ", s)
    s = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>|</h\d>|</li>", "\n", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = html.unescape(s).replace("\xa0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n", s)
    return s


def find_item1(text: str) -> tuple[int, int]:
    starts = [m.start() for m in re.finditer(r"(?i)\n\s*item\s*1\.?\s*(?:\n\s*)?business\b", text)]
    start = starts[1] if len(starts) > 1 else (starts[0] if starts else 0)  # skip table of contents
    m = re.search(r"(?i)\n\s*item\s*1a\.?\s*(?:\n\s*)?risk\s+factors", text[start + 100 :])
    end = start + 100 + m.start() if m else min(len(text), start + 120000)
    return start, end


def competition_passages(text: str, lo: int, hi: int) -> list[dict]:
    out = []
    for m in re.finditer(r"\n\s*(Competition|Competitive Landscape|Competitors|Competitive Environment)\b[^\n]{0,40}\n", text[lo:hi]):
        a = lo + m.start()
        tail = text[a + 20 : min(hi, a + 8000)]
        stop = STOP_HEADINGS.search(tail)
        b = a + 20 + (stop.start() if stop else len(tail))
        out.append({"start": a, "end": b, "text": text[a:b].strip()})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("tickers", nargs="+", help="TICKER or TICKER=search name for reverse mentions")
    ap.add_argument("--max-reverse", type=int, default=40)
    args = ap.parse_args()
    cache = Path(args.cache)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    cfg = yaml.safe_load((ROOT / "config/inflection_research_v1.yaml").read_text())
    decision_time = inf.utc(cfg["timing"]["decision_time_utc"])
    fetcher = CachedFetcher(cache, SEC_USER_AGENT, per_second=5)

    tick = json.loads(gzip.decompress((cache / "sec/company_tickers_exchange.json.gz").read_bytes()))
    cik_of = {row[2]: row[0] for row in tick["data"]}
    for arg in args.tickers:
        t, _, query_name = arg.partition("=")
        cik = cik_of[t]
        sub = json.loads(gzip.decompress((cache / f"sec/submissions/{cik}.json.gz").read_bytes()))
        r = sub["filings"]["recent"]
        best = None
        for form, acc, doc, ts in zip(r["form"], r["accessionNumber"], r["primaryDocument"], r["acceptanceDateTime"]):
            if form != "10-K" or not ts:
                continue
            if inf.utc(ts) <= decision_time and (best is None or ts > best[2]):
                best = (acc, doc, ts)
        rec = {"ticker": t, "cik": cik, "name": sub.get("name")}
        if best:
            acc, doc, ts = best
            url = ARCHIVE.format(cik=cik, acc=acc.replace("-", ""), doc=doc)
            text = html_to_text(fetcher.get(url, f"sec/10k/{cik}_{acc}.htm"))
            lo, hi = find_item1(text)
            rec.update({
                "tenk_url": url, "tenk_accepted": ts,
                "business_intro": text[lo : lo + 6000],
                "competition": competition_passages(text, lo, hi),
            })
        # reverse mentions: other 10-Ks filed in the last 15 months naming the company
        name = query_name or re.sub(r"(?i),?\s+(inc|corp|corporation|holdings|ltd|plc|co|company)\.?$", "", sub.get("name", "")).strip()
        q = quote(f'"{name}"')
        e = decision_time.date().isoformat()
        s = (decision_time.date().replace(year=decision_time.year - 1)).isoformat()
        body = fetcher.get(EFTS.format(q=q, s=s, e=e), f"sec/efts/{t}.json")
        hits = []
        seen = set()
        if body:
            for h in json.loads(body).get("hits", {}).get("hits", []):
                src = h.get("_source", {})
                hit_ciks = [int(c) for c in src.get("ciks") or []]
                acc, _, fname = (h.get("_id") or "").partition(":")
                if not hit_ciks or cik in hit_ciks:
                    continue
                if not fname.endswith((".htm", ".html")) or acc in seen or len(hits) >= args.max_reverse:
                    continue
                seen.add(acc)
                hit = {"names": src.get("display_names"), "cik": hit_ciks[0], "accession": acc, "file": fname,
                       "filed": src.get("file_date"), "in_competition_section": None, "context": ""}
                try:
                    raw = fetcher.get(ARCHIVE.format(cik=hit_ciks[0], acc=acc.replace("-", ""), doc=fname),
                                      f"sec/10k/{hit_ciks[0]}_{acc}_{fname}")
                    htext = html_to_text(raw or b"")
                    hlo, hhi = find_item1(htext)
                    comp = " ".join(p["text"] for p in competition_passages(htext, hlo, hhi))
                    hit["in_competition_section"] = name.lower() in comp.lower()
                    i = htext.lower().find(name.lower())
                    hit["context"] = htext[max(0, i - 250): i + 250] if i >= 0 else ""
                except Exception as exc:  # keep the hit, mark unverified
                    hit["context"] = f"error: {exc}"
                hits.append(hit)
        rec["reverse_mention_query"] = name
        rec["reverse_mentions"] = hits
        (out / f"{t}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1))
        print(t, "10-K" if best else "no 10-K", len(rec.get("competition", [])), "competition passages,",
              len(hits), "reverse hits", flush=True)


if __name__ == "__main__":
    main()
