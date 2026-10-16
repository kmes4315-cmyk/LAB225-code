"""Universe helpers: primary ticker, filer type, shares and prices."""

from __future__ import annotations

import re
import statistics
from datetime import date, datetime, timedelta, timezone

from .inflection import is_available, parse_date

NON_COMMON = re.compile(r"(-P[A-Z]?$|-W[ST]?$|-U$|-R[T]?$|\.W[S]?$|\.U$)")


def primary_ticker(sub: dict, listed: set[str]) -> tuple[str, str] | None:
    for t, ex in zip(sub.get("tickers") or [], sub.get("exchanges") or []):
        if ex not in listed or not t:
            continue
        if NON_COMMON.search(t):
            continue
        if len(t) == 5 and t[-1] in "WUR" and ex == "Nasdaq":
            continue
        return t, ex
    return None


def yahoo_symbol(t: str) -> str:
    return t.replace(".", "-")


def accept_times(sub: dict) -> dict[str, datetime]:
    r = sub.get("filings", {}).get("recent", {})
    out = {}
    for accn, ts in zip(r.get("accessionNumber", []), r.get("acceptanceDateTime", [])):
        if ts:
            out[accn] = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return out


def filer_type(sub: dict, decision_time: datetime, lookback_days: int = 800) -> str:
    r = sub.get("filings", {}).get("recent", {})
    cutoff = decision_time.date() - timedelta(days=lookback_days)
    forms = set()
    for form, fd in zip(r.get("form", []), r.get("filingDate", [])):
        if not fd:
            continue
        d = parse_date(fd)
        if cutoff <= d <= decision_time.date():
            forms.add(form)
    if "10-Q" in forms or "10-K" in forms:
        return "domestic"
    if "20-F" in forms or "40-F" in forms:
        return "foreign"
    return "none"


def sic_code(sub: dict) -> int | None:
    try:
        return int(sub.get("sic") or "")
    except ValueError:
        return None


def is_excluded_industry(sic: int | None, ranges: list[list[int]]) -> bool:
    return sic is not None and any(lo <= sic <= hi for lo, hi in ranges)


def cover_shares(facts: dict, decision_time: datetime, accepts: dict) -> tuple[float | None, str | None, str]:
    """Shares outstanding from the latest cover page filed before the decision time."""
    entries = (
        facts.get("facts", {}).get("dei", {}).get("EntityCommonStockSharesOutstanding", {}).get("units", {}).get("shares", [])
    )
    avail = [e for e in entries if is_available(e, decision_time, accepts)]
    if not avail:
        return None, None, ""
    latest = max(avail, key=lambda e: (e["filed"], e.get("accn", "")))
    same = [e for e in avail if e.get("accn") == latest.get("accn") and e["end"] == latest["end"]]
    vals = sorted({float(e["val"]) for e in same})
    note = "多類股加總" if len(vals) > 1 else ""
    return sum(vals), latest["end"], note


def chart_bars(chart: dict) -> tuple[list[tuple[date, float, float]], list[tuple[date, float]]]:
    res = (chart.get("chart") or {}).get("result") or []
    if not res:
        return [], []
    r = res[0]
    ts = r.get("timestamp") or []
    q = (r.get("indicators", {}).get("quote") or [{}])[0]
    closes, vols = q.get("close") or [], q.get("volume") or []
    bars = []
    for t, c, v in zip(ts, closes, vols):
        if c is None:
            continue
        bars.append((datetime.fromtimestamp(t, timezone.utc).date(), float(c), float(v or 0)))
    splits = []
    for s in ((r.get("events") or {}).get("splits") or {}).values():
        num, den = s.get("numerator"), s.get("denominator")
        if num and den:
            splits.append((datetime.fromtimestamp(s["date"], timezone.utc).date(), float(num) / float(den)))
    return bars, sorted(splits)


def price_on(bars, d: date) -> tuple[date, float] | None:
    best = None
    for bd, c, _ in bars:
        if bd <= d:
            best = (bd, c)
    return best


def median_dollar_volume(bars, d: date, n: int = 20) -> float | None:
    window = [c * v for bd, c, v in bars if bd <= d][-n:]
    return statistics.median(window) if len(window) >= 5 else None


def split_factor_after(splits, after: date, upto: date) -> float:
    f = 1.0
    for sd, ratio in splits:
        if after < sd <= upto:
            f *= ratio
    return f
