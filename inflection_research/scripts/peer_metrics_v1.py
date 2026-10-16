"""Scale comparison for competitor cards: TTM revenue, growth, margins, market cap.

Works for any SEC-listed company in the cache (inside or outside the screen's
market-cap band), using the same point-in-time rules as the screen.

Usage: python scripts/peer_metrics_v1.py --cache DIR TICKER [TICKER ...]
Prints JSON lines.
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import yaml  # noqa: E402

import run_inflection_snapshot_v1 as run  # noqa: E402
from pit_rotation import inflection as inf  # noqa: E402
from pit_rotation import universe as uni  # noqa: E402
from pit_rotation.fsds import load_fsds, supplement  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("tickers", nargs="+")
    args = ap.parse_args()
    cache = Path(args.cache)
    cfg = yaml.safe_load((ROOT / "config/inflection_research_v1.yaml").read_text())
    dt = inf.utc(cfg["timing"]["decision_time_utc"])
    price_date = date.fromisoformat(cfg["timing"]["price_date"])
    tick = json.loads(gzip.decompress((cache / "sec/company_tickers_exchange.json.gz").read_bytes()))
    cik_of = {r[2]: r[0] for r in tick["data"]}
    fsds = {}
    for q in run.FSDS_QUARTERS:
        p = cache / f"sec/fsds/{q}.zip.gz"
        for c, tags in load_fsds(gzip.decompress(p.read_bytes()), run.FSDS_TAGS).items():
            for k, v in tags.items():
                fsds.setdefault(c, {}).setdefault(k, []).extend(v)
    for t in args.tickers:
        cik = cik_of.get(t)
        if cik is None:
            print(json.dumps({"ticker": t, "error": "不在 SEC 代號清單（可能未上市或外國公司）"}, ensure_ascii=False))
            continue
        sub = run.load_gz_json(cache / f"sec/submissions/{cik}.json.gz") or {}
        facts = run.load_gz_json(cache / f"sec/companyfacts/{cik}.json.gz")
        facts, _ = supplement(facts, fsds.get(cik))
        res = run.screen_company(facts, uni.accept_times(sub), dt, cfg) if facts else {}
        chart = run.load_gz_json(cache / f"yahoo/chart/{uni.yahoo_symbol(t)}.json.gz")
        bars, splits = uni.chart_bars(chart or {})
        px = uni.price_on(bars, price_date)
        shares, asof, _ = uni.cover_shares(facts or {}, dt, uni.accept_times(sub))
        mcap = shares * uni.split_factor_after(splits, date.fromisoformat(asof), price_date) * px[1] if shares and px else None
        g2, g3, g4 = res.get("g2"), res.get("g3"), res.get("g4")
        print(json.dumps({
            "ticker": t, "name": sub.get("name"), "sic": sub.get("sicDescription"),
            "filer": uni.filer_type(sub, dt),
            "last_quarter_end": res.get("last_quarter_end"),
            "ttm_revenue_musd": round(res["ttm_revenue"] / 1e6, 1) if res.get("ttm_revenue") else None,
            "ttm_growth": round(g2.value, 3) if g2 and g2.value is not None else None,
            "accel_pp": round(g3.value, 1) if g3 and g3.value is not None else None,
            "yoy_path": g3.detail if g3 else None,
            "ttm_gross_margin": round(res["ttm_gross_margin"], 3) if res.get("ttm_gross_margin") is not None else None,
            "ttm_op_margin": round(res["ttm_op_margin"], 3) if res.get("ttm_op_margin") is not None else None,
            "op_margin_change_pp": round(g4.value, 1) if g4 and g4.value is not None else None,
            "market_cap_busd": round(mcap / 1e9, 2) if mcap else None,
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
