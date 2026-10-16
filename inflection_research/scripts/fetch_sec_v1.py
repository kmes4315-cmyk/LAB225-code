"""Download SEC data for the v1 snapshot into the cache.

Phase 1: ticker/exchange list.
Phase 2: submissions JSON for every CIK listed on a US exchange.
Phase 3: XBRL companyfacts for every operating company among them.

Usage: python scripts/fetch_sec_v1.py --cache DIR [--phase 1|2|3|all]
"""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import yaml  # noqa: E402

from pit_rotation.fetch import SEC_USER_AGENT, CachedFetcher  # noqa: E402

TICKERS_URL = "https://www.sec.gov/files/company_tickers_exchange.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"


def listed_ciks(fetcher: CachedFetcher, exchanges: set[str]) -> list[int]:
    data = json.loads(fetcher.get(TICKERS_URL, "sec/company_tickers_exchange.json"))
    ciks = sorted({row[0] for row in data["data"] if row[3] in exchanges})
    return ciks


def run_parallel(fetcher, jobs, label, workers=14):
    done = 0
    failed = []
    with ThreadPoolExecutor(workers) as pool:
        futures = {pool.submit(fetcher.get, url, key): key for url, key in jobs}
        for fut in as_completed(futures):
            done += 1
            try:
                fut.result()
            except Exception as exc:  # keep going; failures are listed at the end
                failed.append((futures[fut], str(exc)))
            if done % 250 == 0:
                print(f"[{label}] {done}/{len(jobs)}", flush=True)
    print(f"[{label}] finished {done}/{len(jobs)}, failed {len(failed)}", flush=True)
    for key, err in failed[:20]:
        print("  FAILED", key, err, flush=True)
    return failed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--phase", default="all")
    args = ap.parse_args()

    cfg = yaml.safe_load((ROOT / "config/inflection_research_v1.yaml").read_text())
    fetcher = CachedFetcher(Path(args.cache), SEC_USER_AGENT, per_second=8)
    ciks = listed_ciks(fetcher, set(cfg["universe"]["exchanges"]))
    print(f"listed CIKs: {len(ciks)}", flush=True)

    if args.phase in ("2", "all"):
        jobs = [(SUBMISSIONS_URL.format(cik=c), f"sec/submissions/{c}.json") for c in ciks]
        run_parallel(fetcher, jobs, "submissions")

    if args.phase in ("3", "all"):
        operating = []
        for c in ciks:
            body = fetcher.get(SUBMISSIONS_URL.format(cik=c), f"sec/submissions/{c}.json")
            if body is None:
                continue
            sub = json.loads(body)
            if sub.get("entityType") == "operating":
                operating.append(c)
        print(f"operating CIKs: {len(operating)}", flush=True)
        jobs = [(FACTS_URL.format(cik=c), f"sec/companyfacts/{c}.json") for c in operating]
        run_parallel(fetcher, jobs, "companyfacts")


if __name__ == "__main__":
    main()
