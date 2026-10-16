"""Quarterly inflection snapshot (v1): universe, gates, candidates, append-only record.

Usage: python scripts/run_inflection_snapshot_v1.py --cache DIR [--out DIR] [--period YYYY-MM-DD]

Reads only cached SEC/Yahoo data, so rerunning with the same cache gives
byte-identical outputs.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import yaml  # noqa: E402

from pit_rotation import inflection as inf  # noqa: E402
from pit_rotation import universe as uni  # noqa: E402
from pit_rotation.records import sha256_bytes, write_period  # noqa: E402

GATE_KEYS = ["g1", "g2", "g3", "g4", "g5", "g6"]


def load_gz_json(p: Path):
    return json.loads(gzip.decompress(p.read_bytes())) if p.exists() else None


def periods_for(facts, concept, unit, decision_time, accepts, taxonomy="us-gaap"):
    entries = facts.get("facts", {}).get(taxonomy, {}).get(concept, {}).get("units", {}).get(unit, [])
    return inf.latest_by_period(entries, decision_time, accepts)


def merged_quarters(facts, concepts, unit, decision_time, accepts, additive=True):
    per = {c: periods_for(facts, c, unit, decision_time, accepts) for c in concepts}
    merged, used = inf.merge_concepts(per, concepts)
    return inf.quarterly_from_periods(merged, additive=additive), merged, used


def has_non_usd_revenue_only(facts) -> bool:
    gaap = facts.get("facts", {}).get("us-gaap", {})
    units = set()
    for c in inf.REVENUE_CONCEPTS:
        units |= set(gaap.get(c, {}).get("units", {}).keys())
    return bool(units) and "USD" not in units


def fmt(x, nd=4):
    if x is None:
        return ""
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    return str(x)


def to_csv(rows: list[dict], cols: list[str]) -> bytes:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: fmt(r.get(k)) for k in cols})
    return buf.getvalue().encode("utf-8")


def screen_company(facts, accepts, decision_time, cfg) -> dict:
    g = cfg["gates"]
    out: dict = {}
    if facts is None:
        out["g1"] = inf.GateResult(inf.NA, None, "沒有 XBRL 財報")
        return out
    if has_non_usd_revenue_only(facts):
        out["g1"] = inf.GateResult(inf.FAIL, None, "非美元申報")
        return out

    rev, _, rev_used = merged_quarters(facts, inf.REVENUE_CONCEPTS, "USD", decision_time, accepts)
    out["revenue_concepts"] = "+".join(rev_used)
    g1 = inf.gate_revenue_quarters(rev, cfg["universe"]["min_revenue_quarters"])
    if rev:
        last = max(rev)
        out["last_quarter_end"] = last.isoformat()
        stale = (decision_time.date() - last).days > cfg["interpretations"]["max_staleness_days"]
        if stale:
            g1 = inf.GateResult(inf.NA, g1.value, f"最新一季 {last} 已過期")
    out["g1"] = g1
    out["n_quarters"] = g1.value
    if g1.status != inf.PASS:
        return out

    opi, _, _ = merged_quarters(facts, ["OperatingIncomeLoss"], "USD", decision_time, accepts)
    gp, _, _ = merged_quarters(facts, ["GrossProfit"], "USD", decision_time, accepts)
    if not gp:
        cost, _, _ = merged_quarters(facts, inf.COST_OF_REVENUE_CONCEPTS, "USD", decision_time, accepts)
        gp = {e: inf.Quarter(q.start, q.end, q.val - cost[e].val, True) for e, q in rev.items() if e in cost}
    ocf, _, _ = merged_quarters(facts, inf.OCF_CONCEPTS, "USD", decision_time, accepts)
    dil_per = {c: periods_for(facts, c, "shares", decision_time, accepts) for c in inf.DILUTED_SHARES_CONCEPTS}
    dil_merged, _ = inf.merge_concepts(dil_per, inf.DILUTED_SHARES_CONCEPTS)
    imp, _, _ = merged_quarters(facts, inf.IMPAIRMENT_CONCEPTS[:1], "USD", decision_time, accepts)
    imp2, _, _ = merged_quarters(facts, inf.IMPAIRMENT_CONCEPTS[1:], "USD", decision_time, accepts)
    acq, _, _ = merged_quarters(facts, ["PaymentsToAcquireBusinessesNetOfCashAcquired"], "USD", decision_time, accepts)
    sin = inf.ScreenInput(
        revenue=rev,
        op_income=opi,
        gross_profit=gp,
        ocf=ocf,
        diluted_q=inf.quarterly_from_periods(dil_merged, additive=False),
        diluted_fy=inf.annual_from_periods(dil_merged),
    )
    last = max(rev)
    out["g2"] = inf.gate_ttm_growth(rev, last, g["g2_ttm_revenue_yoy_min"])
    out["g3"] = inf.gate_acceleration(rev, last, g["g3_acceleration_min_pp"])
    out["g4"] = inf.gate_profit_inflection(rev, opi, last, g["g4_ttm_op_margin_change_min_pp"])
    out["g5"] = inf.gate_cash_flow(ocf, rev, last)
    out["g6"] = inf.gate_dilution(sin, last, g["g6_diluted_share_growth_max"])

    out["ttm_revenue"] = inf.ttm(rev, last)
    out["latest_q_revenue"] = rev[last].val
    out["latest_q_yoy"] = inf.yoy(rev, last)
    yago = inf.year_ago(rev, last)
    gm_now = inf.ttm_margin(gp, rev, last)
    gm_prev = inf.ttm_margin(gp, rev, yago.end) if yago else None
    out["ttm_gross_margin"] = gm_now
    out["gm_change_pp"] = (gm_now - gm_prev) * 100 if gm_now is not None and gm_prev is not None else None
    out["ttm_op_margin"] = inf.ttm_margin(opi, rev, last)

    # Labels for manual review (not gates): one-off impairments and acquisitions.
    total_imp = {}
    for series in (imp, imp2):
        for e, q in series.items():
            total_imp[e] = inf.Quarter(q.start, q.end, total_imp.get(e, inf.Quarter(q.start, q.end, 0.0)).val + q.val)
    imp_now = sum(q.val for q in (inf.contiguous_chain(total_imp, last, 4) or []) ) if last in total_imp else 0.0
    imp_prev = 0.0
    if yago and yago.end in total_imp:
        imp_prev = sum(q.val for q in (inf.contiguous_chain(total_imp, yago.end, 4) or []))
    out["ttm_impairment"] = imp_now
    out["ttm_impairment_prior"] = imp_prev
    oi_now, oi_prev = inf.ttm(opi, last), inf.ttm(opi, yago.end) if yago else None
    rv_now, rv_prev = inf.ttm(rev, last), inf.ttm(rev, yago.end) if yago else None
    if None not in (oi_now, oi_prev, rv_now, rv_prev) and rv_now > 0 and rv_prev > 0:
        out["op_margin_change_ex_impairment_pp"] = (
            (oi_now + imp_now) / rv_now - (oi_prev + imp_prev) / rv_prev
        ) * 100
    acq_ttm = inf.ttm(acq, last) if last in acq else None
    out["acquisition_share_of_revenue"] = (acq_ttm / rv_now) if acq_ttm and rv_now else None

    req = inf.next_quarter_requirement(rev, last, g["g2_ttm_revenue_yoy_min"])
    if req:
        out.update({f"next_{k}": v for k, v in req.items()})
    out["latest_filed"] = rev[last].filed
    if rev[last].filed:
        lag = (inf.parse_date(rev[last].filed) - last).days
        out["next_report_expected"] = (last + timedelta(days=91 + max(lag, 0))).isoformat()
    out["_quarters"] = {"revenue": rev, "op_income": opi, "gross_profit": gp, "ocf": ocf}
    return out


def code_version() -> str:
    h = hashlib.sha256()
    for p in sorted(list((ROOT / "src").rglob("*.py")) + list((ROOT / "scripts").glob("*.py"))):
        h.update(p.relative_to(ROOT).as_posix().encode())
        h.update(p.read_bytes())
    return h.hexdigest()


def data_version(cache: Path) -> tuple[str, int]:
    latest = {}
    log = cache / "fetch_log.jsonl"
    for line in log.read_text().splitlines():
        rec = json.loads(line)
        latest[rec["key"]] = rec["sha256"]
    h = hashlib.sha256()
    for k in sorted(latest):
        h.update(f"{k}:{latest[k]}\n".encode())
    return h.hexdigest(), len(latest)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--out", default=str(ROOT / "data/prospective/inflection_v1"))
    ap.add_argument("--period", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    cache = Path(args.cache)

    cfg_bytes = (ROOT / "config/inflection_research_v1.yaml").read_bytes()
    cfg = yaml.safe_load(cfg_bytes)
    decision_time = inf.utc(cfg["timing"]["decision_time_utc"])
    price_date = date.fromisoformat(cfg["timing"]["price_date"])
    period = args.period or decision_time.date().isoformat()
    listed = set(cfg["universe"]["exchanges"])
    ucfg = cfg["universe"]

    spy_bars, _ = uni.chart_bars(load_gz_json(cache / "yahoo/chart/SPY.json.gz") or {})
    rs_months = cfg["gates"]["g7_relative_strength_months"]
    rs_start = price_date - timedelta(days=round(rs_months * 30.44))
    spy_now, spy_then = uni.price_on(spy_bars, price_date), uni.price_on(spy_bars, rs_start)
    spy_ret = spy_now[1] / spy_then[1] - 1.0 if spy_now and spy_then else None

    tickers = json.loads(gzip.decompress((cache / "sec/company_tickers_exchange.json.gz").read_bytes()))
    ciks = sorted({row[0] for row in tickers["data"] if row[3] in listed})

    universe_rows, screened = [], []
    for cik in ciks:
        sub = load_gz_json(cache / f"sec/submissions/{cik}.json.gz")
        if not sub or sub.get("entityType") != "operating":
            continue
        pt = uni.primary_ticker(sub, listed)
        if not pt:
            continue
        ticker, exchange = pt
        accepts = uni.accept_times(sub)
        sic = uni.sic_code(sub)
        ftype = uni.filer_type(sub, decision_time)
        facts = load_gz_json(cache / f"sec/companyfacts/{cik}.json.gz")
        chart = load_gz_json(cache / f"yahoo/chart/{uni.yahoo_symbol(ticker)}.json.gz")
        bars, splits = uni.chart_bars(chart or {})
        px = uni.price_on(bars, price_date)

        shares, shares_asof, shares_note = (None, None, "")
        if facts:
            shares, shares_asof, shares_note = uni.cover_shares(facts, decision_time, accepts)
            basic = inf.quarterly_from_periods(
                periods_for(facts, "WeightedAverageNumberOfSharesOutstandingBasic", "shares", decision_time, accepts),
                additive=False,
            )
            if basic:
                b_last = basic[max(basic)]
                if shares is None or b_last.val > 1.5 * shares:
                    shares, shares_asof = b_last.val, b_last.end.isoformat()
                    shares_note = (shares_note + " 用基本加權股數").strip()
        mcap = None
        if shares and px:
            adj = uni.split_factor_after(splits, date.fromisoformat(shares_asof), price_date)
            mcap = shares * adj * px[1]
        in_band = mcap is not None and ucfg["market_cap_min_usd"] <= mcap <= ucfg["market_cap_max_usd"]
        financial = uni.is_excluded_industry(sic, ucfg["excluded_sic_ranges"])

        if mcap is None:
            scope = "缺市值"
        elif not in_band:
            scope = "市值區間外"
        elif financial:
            scope = "排除：金融與不動產"
        elif ftype == "foreign":
            scope = "外國申報（無季度 XBRL）"
        elif ftype == "none":
            scope = "觀察：尚無定期報告"
        else:
            scope = "篩選"

        ret6 = None
        then = uni.price_on(bars, rs_start)
        if px and then and then[0] >= rs_start - timedelta(days=7):
            ret6 = px[1] / then[1] - 1.0
        row = {
            "cik": cik,
            "ticker": ticker,
            "name": sub.get("name", ""),
            "exchange": exchange,
            "sic": sic,
            "sic_description": sub.get("sicDescription", ""),
            "filer_type": ftype,
            "price_date_used": px[0].isoformat() if px else "",
            "price": px[1] if px else None,
            "shares": shares,
            "shares_asof": shares_asof,
            "shares_note": shares_note,
            "market_cap": mcap,
            "median_dollar_volume_20d": uni.median_dollar_volume(bars, price_date) if bars else None,
            "return_6m": ret6,
            "excess_return_6m": (ret6 - spy_ret) if ret6 is not None and spy_ret is not None else None,
            "in_cap_band": in_band,
            "scope": scope,
        }
        universe_rows.append(row)
        if scope == "篩選":
            res = screen_company(facts, accepts, decision_time, cfg)
            screened.append((row, res))

    # Relative strength percentile within the screened universe (label only).
    rs_vals = sorted(r["excess_return_6m"] for r, _ in screened if r["excess_return_6m"] is not None)
    for r, _ in screened:
        x = r["excess_return_6m"]
        r["rs_percentile"] = (
            None if x is None else sum(1 for v in rs_vals if v <= x) / len(rs_vals) * 100
        )

    # Industry sync proxy: share of same-SIC peers in scope whose revenue is accelerating.
    by_sic = defaultdict(list)
    for r, res in screened:
        g3 = res.get("g3")
        if g3 is not None and g3.status != inf.NA and r["sic"]:
            by_sic[r["sic"]].append((r["cik"], g3.status == inf.PASS))

    detail_rows, cand_rows, watch_rows, quarter_rows = [], [], [], []
    for r, res in screened:
        d = dict(r)
        for k in GATE_KEYS:
            gr = res.get(k)
            d[f"{k}_status"] = gr.status if gr else ""
            d[f"{k}_value"] = gr.value if gr else None
            d[f"{k}_detail"] = gr.detail if gr else ""
        for k in [
            "revenue_concepts", "last_quarter_end", "n_quarters", "ttm_revenue", "latest_q_revenue", "latest_q_yoy",
            "ttm_gross_margin", "gm_change_pp", "ttm_op_margin", "ttm_impairment", "ttm_impairment_prior",
            "op_margin_change_ex_impairment_pp", "acquisition_share_of_revenue", "latest_filed",
            "next_report_expected", "next_revenue_needed", "next_yoy_needed",
        ]:
            d[k] = res.get(k)
        peers = [ok for c, ok in by_sic.get(r["sic"], []) if c != r["cik"]]
        d["sic_peers_n"] = len(peers)
        d["sic_peers_accel_share"] = (sum(peers) / len(peers)) if len(peers) >= 3 else None

        hard = all(res.get(k) is not None and res[k].status == inf.PASS for k in ["g1", "g2", "g3", "g4", "g6"])
        g5 = res.get("g5")
        soft_ok = g5 is not None and g5.status in (inf.PASS, inf.NA)
        if hard and soft_ok:
            d["result"] = "入選"
            d["flags"] = "；".join(
                f
                for f in [
                    "現金流待確認" if g5.status == inf.NA else "",
                    "TTM 含減損" if (res.get("ttm_impairment") or 0) > 0 or (res.get("ttm_impairment_prior") or 0) > 0 else "",
                    "可能含併購" if (res.get("acquisition_share_of_revenue") or 0) > 0.10 else "",
                    "相對強勢低於中位數" if (r.get("rs_percentile") or 100) < 50 else "",
                ]
                if f
            )
            v, h, q = inf.classify_source(d["gm_change_pp"], d["sic_peers_accel_share"], cfg["source_classification"])
            d.update({"source_vertical": v, "source_horizontal": h, "source_quadrant": q})
            cand_rows.append(d)
        else:
            reasons = [
                f"{k}:{res[k].status}" for k in GATE_KEYS if res.get(k) is not None and res[k].status != inf.PASS
            ]
            d["result"] = "排除" if res.get("g1") and res["g1"].status == inf.PASS else "資料不足"
            d["flags"] = " ".join(reasons)
            if res.get("g1") and res["g1"].status == inf.FAIL and "非美元" not in res["g1"].detail:
                watch_rows.append({**d, "watch_reason": f"營收資料只有 {res['g1'].value} 季（< 7 季）"})
        detail_rows.append(d)
        for series_name, series in (res.get("_quarters") or {}).items():
            for e in sorted(series):
                q = series[e]
                quarter_rows.append(
                    {"cik": r["cik"], "ticker": r["ticker"], "series": series_name, "start": q.start.isoformat(),
                     "end": e.isoformat(), "value": q.val, "derived": int(q.derived)}
                )
    for r in universe_rows:
        if r["scope"] == "觀察：尚無定期報告":
            watch_rows.append({**r, "watch_reason": "尚無 10-Q/10-K（新上市）"})

    # Rank inside each source group by acceleration and margin improvement.
    groups = defaultdict(list)
    for d in cand_rows:
        groups[d["source_quadrant"]].append(d)
    for grp in groups.values():
        n = len(grp)
        acc = sorted(grp, key=lambda x: -x["g3_value"])
        mar = sorted(grp, key=lambda x: -x["g4_value"])
        for d in grp:
            d["group_rank_score"] = ((acc.index(d) + 1) + (mar.index(d) + 1)) / 2 / n
        for i, d in enumerate(sorted(grp, key=lambda x: (x["group_rank_score"], x["ticker"]))):
            d["group_rank"] = i + 1
    cand_rows.sort(key=lambda d: (d["source_quadrant"], d["group_rank"]))

    changes = [{"ticker": d["ticker"], "change": "新進", "state": "入選", "detail": d["source_quadrant"]} for d in cand_rows]
    tracking = [
        {"ticker": d["ticker"], "cik": d["cik"], "entry_date": period, "state": "入選", "entry_price": d["price"],
         "entry_price_date": d["price_date_used"], "next_report_expected": d["next_report_expected"]}
        for d in cand_rows
    ]

    ucols = ["cik", "ticker", "name", "exchange", "sic", "sic_description", "filer_type", "price_date_used", "price",
             "shares", "shares_asof", "shares_note", "market_cap", "median_dollar_volume_20d", "return_6m",
             "excess_return_6m", "in_cap_band", "scope"]
    dcols = ucols + ["rs_percentile", "result", "flags"] + [f"{k}_{s}" for k in GATE_KEYS for s in ("status", "value", "detail")] + [
        "revenue_concepts", "last_quarter_end", "n_quarters", "ttm_revenue", "latest_q_revenue", "latest_q_yoy",
        "ttm_gross_margin", "gm_change_pp", "ttm_op_margin", "ttm_impairment", "ttm_impairment_prior",
        "op_margin_change_ex_impairment_pp", "acquisition_share_of_revenue", "sic_peers_n", "sic_peers_accel_share",
        "latest_filed", "next_report_expected", "next_revenue_needed", "next_yoy_needed"]
    ccols = ["source_quadrant", "group_rank", "ticker", "name", "market_cap", "price", "g2_value", "g3_value", "g3_detail",
             "g4_value", "g4_detail", "g5_status", "g5_detail", "g6_value", "rs_percentile", "gm_change_pp",
             "source_vertical", "source_horizontal", "sic_description", "sic_peers_n", "sic_peers_accel_share",
             "flags", "ttm_revenue", "ttm_op_margin", "op_margin_change_ex_impairment_pp",
             "acquisition_share_of_revenue", "last_quarter_end", "latest_filed", "next_report_expected",
             "next_revenue_needed", "next_yoy_needed", "cik"]
    wcols = ["ticker", "name", "market_cap", "sic_description", "watch_reason", "cik"]

    universe_rows.sort(key=lambda r: r["cik"])
    detail_rows.sort(key=lambda r: r["cik"])
    watch_rows.sort(key=lambda r: r["ticker"])
    quarter_rows.sort(key=lambda r: (r["cik"], r["series"], r["end"]))
    qbuf = to_csv(quarter_rows, ["cik", "ticker", "series", "start", "end", "value", "derived"])
    files = {
        "universe_snapshot.csv": to_csv(universe_rows, ucols),
        "gate_details.csv": to_csv(detail_rows, dcols),
        "candidates.csv": to_csv(cand_rows, ccols),
        "watchlist.csv": to_csv(watch_rows, wcols),
        "changes.csv": to_csv(changes, ["ticker", "change", "state", "detail"]),
        "tracking.csv": to_csv(tracking, ["ticker", "cik", "entry_date", "state", "entry_price", "entry_price_date",
                                          "next_report_expected"]),
        "quarterly_inputs.csv.gz": gzip.compress(qbuf, mtime=0),
    }
    dv, n_objects = data_version(cache)
    meta = {
        "decision_time_utc": cfg["timing"]["decision_time_utc"],
        "price_date": cfg["timing"]["price_date"],
        "config_sha256": sha256_bytes(cfg_bytes),
        "code_sha256": code_version(),
        "data_sha256": dv,
        "data_objects": n_objects,
        "spy_return_6m": spy_ret,
        "counts": {
            "listed_operating": len(universe_rows),
            "in_cap_band": sum(1 for r in universe_rows if r["in_cap_band"]),
            "screened": len(screened),
            "candidates": len(cand_rows),
            "watchlist": len(watch_rows),
        },
    }
    print(json.dumps(meta, indent=2, ensure_ascii=False))
    if args.dry_run:
        out = Path(args.out) / "_dry_run"
        out.mkdir(parents=True, exist_ok=True)
        for name, b in files.items():
            (out / name).write_bytes(b)
        print("dry run written to", out)
        return
    manifest = write_period(Path(args.out), period, files, meta)
    print("recorded", period, json.dumps(manifest["files"], indent=2))


if __name__ == "__main__":
    main()
