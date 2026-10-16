"""Download daily prices (close, volume, splits) from Yahoo for every operating company.

Usage: python scripts/fetch_prices_v1.py --cache DIR
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import yaml  # noqa: E402

from pit_rotation.fetch import BROWSER_USER_AGENT, CachedFetcher  # noqa: E402

CHART_URL = (
    "https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
    "?period1={p1}&period2={p2}&interval=1d&events=split&includeAdjustedClose=true"
)
NON_COMMON = re.compile(r"(-P[A-Z]?$|-W[ST]?$|-U$|-R[T]?$|\.W[S]?$|\.U$)")


def primary_ticker(sub: dict, listed: set[str]) -> str | None:
    pairs = list(zip(sub.get("tickers") or [], sub.get("exchanges") or []))
    for t, ex in pairs:
        if ex not in listed or not t:
            continue
        if NON_COMMON.search(t):
            continue
        if len(t) == 5 and t[-1] in "WUR" and ex == "Nasdaq":
            continue
        return t
    return None


def yahoo_symbol(t: str) -> str:
    return t.replace(".", "-")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    args = ap.parse_args()
    cache = Path(args.cache)
    cfg = yaml.safe_load((ROOT / "config/inflection_research_v1.yaml").read_text())
    listed = set(cfg["universe"]["exchanges"])

    tickers = ["SPY"]
    for p in sorted((cache / "sec/submissions").glob("*.json.gz")):
        import gzip

        sub = json.loads(gzip.decompress(p.read_bytes()))
        if sub.get("entityType") != "operating":
            continue
        t = primary_ticker(sub, listed)
        if t:
            tickers.append(t)
    tickers = sorted(set(tickers))
    print(f"tickers: {len(tickers)}", flush=True)

    p1 = int(datetime(2025, 3, 1, tzinfo=timezone.utc).timestamp())
    p2 = int(datetime(2026, 10, 16, tzinfo=timezone.utc).timestamp())
    fetcher = CachedFetcher(cache, BROWSER_USER_AGENT, per_second=4)
    failed = []
    done = 0
    with ThreadPoolExecutor(4) as pool:
        futs = {
            pool.submit(
                fetcher.get, CHART_URL.format(sym=yahoo_symbol(t), p1=p1, p2=p2), f"yahoo/chart/{yahoo_symbol(t)}.json"
            ): t
            for t in tickers
        }
        for f in as_completed(futs):
            done += 1
            try:
                f.result()
            except Exception as exc:
                failed.append((futs[f], str(exc)))
            if done % 250 == 0:
                print(f"[prices] {done}/{len(tickers)}", flush=True)
    print(f"[prices] finished, failed {len(failed)}", flush=True)
    for t, e in failed[:30]:
        print("  FAILED", t, e, flush=True)


if __name__ == "__main__":
    main()
