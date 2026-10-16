"""Growth-inflection screen v1: point-in-time fact handling and gate logic.

Pure computation only: no account data, no orders.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

QUARTER_DAYS = (80, 100)
HALF_DAYS = (170, 195)
NINE_MONTH_DAYS = (260, 285)
ANNUAL_DAYS = (350, 380)
CONTIGUITY_TOLERANCE_DAYS = 7
YEAR_AGO_TOLERANCE_DAYS = 12
RESTATEMENT_THRESHOLD = 0.02  # smaller revisions are routine reclassifications

REVENUE_CONCEPTS = [
    "Revenues",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
    "SalesRevenueNet",
    "SalesRevenueGoodsNet",
    "SalesRevenueServicesNet",
    "RevenuesNetOfInterestExpense",
]
COST_OF_REVENUE_CONCEPTS = [
    "CostOfRevenue",
    "CostOfGoodsAndServicesSold",
    "CostOfGoodsSold",
    "CostOfServices",
    "CostOfGoodsAndServiceExcludingDepreciationDepletionAndAmortization",
]
OCF_CONCEPTS = [
    "NetCashProvidedByUsedInOperatingActivities",
    "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
]
DILUTED_SHARES_CONCEPTS = [
    "WeightedAverageNumberOfDilutedSharesOutstanding",
    "WeightedAverageNumberOfShareOutstandingBasicAndDiluted",
]
IMPAIRMENT_CONCEPTS = [
    "GoodwillImpairmentLoss",
    "ImpairmentOfIntangibleAssetsExcludingGoodwill",
    "ImpairmentOfIntangibleAssetsIndefinitelivedExcludingGoodwill",
    "ImpairmentOfIntangibleAssetsFinitelived",
]


def parse_date(s: str) -> date:
    return date.fromisoformat(s)


def days(start: date, end: date) -> int:
    return (end - start).days + 1


def in_range(n: int, bounds: tuple[int, int]) -> bool:
    return bounds[0] <= n <= bounds[1]


# ---------------------------------------------------------------------------
# Point-in-time filtering
# ---------------------------------------------------------------------------

def is_available(entry: dict, decision_time: datetime, accept_times: dict[str, datetime]) -> bool:
    """A fact is usable only if its filing was accepted before the decision time.

    Filings dated before the decision date are always earlier. For a filing
    dated on the decision date we need the acceptance timestamp; without one
    the fact is rejected.
    """
    filed = parse_date(entry["filed"])
    decision_date = decision_time.astimezone(timezone.utc).date()
    if filed < decision_date:
        return True
    if filed > decision_date:
        return False
    accepted = accept_times.get(entry.get("accn", ""))
    return accepted is not None and accepted <= decision_time


def latest_by_period(entries: list[dict], decision_time: datetime, accept_times=None) -> dict:
    """Map (start, end) -> entry, keeping the last version filed before the decision time."""
    accept_times = accept_times or {}
    best: dict = {}
    first: dict = {}
    for e in entries:
        if not is_available(e, decision_time, accept_times):
            continue
        key = (e.get("start"), e["end"])
        order = (e["filed"], e.get("accn", ""))
        cur = best.get(key)
        if cur is None or order > (cur["filed"], cur.get("accn", "")):
            best[key] = e
        f = first.get(key)
        if f is None or order < (f["filed"], f.get("accn", "")):
            first[key] = e
    out = {}
    for key, e in best.items():
        e = dict(e)
        f0 = float(first[key]["val"])
        e["restated"] = abs(float(e["val"]) - f0) > RESTATEMENT_THRESHOLD * max(abs(f0), 1.0)
        out[key] = e
    return out


def merge_concepts(per_concept: dict[str, dict], priority: list[str]) -> tuple[dict, list[str]]:
    """Merge period maps from several XBRL tags for the same line item.

    The primary tag is the one with the latest period end (ties: larger value).
    Another tag may only fill gaps if every period both tags report agrees
    within 0.5%, and they share at least one period.
    """
    present = [c for c in priority if per_concept.get(c)]
    if not present:
        return {}, []

    def score(c):
        m = per_concept[c]
        last_end = max(k[1] for k in m)
        last_val = max(abs(v["val"]) for k, v in m.items() if k[1] == last_end)
        return (last_end, last_val)

    primary = max(present, key=score)
    merged = dict(per_concept[primary])
    used = [primary]
    for c in present:
        if c == primary:
            continue
        other = per_concept[c]
        overlap = [k for k in other if k in merged]
        if not overlap:
            continue
        consistent = all(
            abs(other[k]["val"] - merged[k]["val"]) <= 0.005 * max(abs(merged[k]["val"]), 1.0)
            for k in overlap
        )
        if not consistent:
            continue
        added = False
        for k, v in other.items():
            if k not in merged:
                merged[k] = v
                added = True
        if added:
            used.append(c)
    return merged, used


# ---------------------------------------------------------------------------
# Quarterly series
# ---------------------------------------------------------------------------

@dataclass
class Quarter:
    start: date
    end: date
    val: float
    derived: bool = False
    filed: str = ""
    restated: bool = False


def quarterly_from_periods(periods: dict, additive: bool = True) -> dict[date, Quarter]:
    """Build discrete quarters from duration facts.

    Direct 3-month facts are used as is. For additive items, missing quarters
    are derived from cumulative facts that share a start date (6M-3M, 9M-6M,
    FY-9M, or FY minus three tiled quarters). Non-additive items (weighted
    share counts) only use direct quarters.
    """
    dur = []
    for (s, e), entry in periods.items():
        if s is None:
            continue
        sd, ed = parse_date(s), parse_date(e)
        dur.append((sd, ed, float(entry["val"]), entry.get("filed", ""), bool(entry.get("restated"))))

    quarters: dict[date, Quarter] = {}
    for sd, ed, v, f, r in dur:
        if in_range(days(sd, ed), QUARTER_DAYS):
            q = quarters.get(ed)
            if q is None or f > q.filed:
                quarters[ed] = Quarter(sd, ed, v, False, f, r)
    if not additive:
        return quarters

    by_start: dict[date, list] = {}
    for sd, ed, v, f, r in dur:
        by_start.setdefault(sd, []).append((ed, v, f, r))
    for sd, items in by_start.items():
        items.sort()
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                a_end, a_val, a_f, a_r = items[i]
                b_end, b_val, b_f, b_r = items[j]
                q_start = a_end + timedelta(days=1)
                if not in_range(days(q_start, b_end), QUARTER_DAYS) or b_end in quarters:
                    continue
                if mixed_vintage((a_f, a_r), (b_f, b_r)):
                    continue
                quarters[b_end] = Quarter(q_start, b_end, b_val - a_val, True, max(a_f, b_f), a_r or b_r)

    # Q4 = FY - (Q1 + Q2 + Q3) when the three quarters tile the year's first nine months.
    for sd, ed, v, f, r in dur:
        if not in_range(days(sd, ed), ANNUAL_DAYS) or ed in quarters:
            continue
        chain = tile_from(quarters, sd, 3)
        if chain and in_range(days(chain[-1].end + timedelta(days=1), ed), QUARTER_DAYS):
            if any(mixed_vintage((q.filed, q.restated), (f, r)) for q in chain):
                continue
            q_start = chain[-1].end + timedelta(days=1)
            quarters[ed] = Quarter(q_start, ed, v - sum(q.val for q in chain), True, f, r)
    return quarters


def mixed_vintage(a: tuple[str, bool], b: tuple[str, bool]) -> bool:
    """True when one operand was restated after the other was last reported.

    Subtracting a restated cumulative figure from an unrestated one (or the
    reverse) mixes two reporting bases, e.g. before and after a business was
    moved to discontinued operations, so such a quarter is left blank.
    """
    (fa, ra), (fb, rb) = a, b
    return (ra and fa > fb) or (rb and fb > fa)


def tile_from(quarters: dict[date, Quarter], start: date, n: int) -> list[Quarter] | None:
    chain = []
    cursor = start
    for _ in range(n):
        nxt = None
        for q in quarters.values():
            if abs((q.start - cursor).days) <= CONTIGUITY_TOLERANCE_DAYS:
                nxt = q
                break
        if nxt is None:
            return None
        chain.append(nxt)
        cursor = nxt.end + timedelta(days=1)
    return chain


def contiguous_chain(quarters: dict[date, Quarter], last_end: date, n: int) -> list[Quarter] | None:
    """Return n contiguous quarters ending at last_end (oldest first), or None."""
    if last_end not in quarters:
        return None
    chain = [quarters[last_end]]
    while len(chain) < n:
        want_end = chain[0].start - timedelta(days=1)
        prev = None
        for e, q in quarters.items():
            gap = abs((e - want_end).days)
            if gap <= CONTIGUITY_TOLERANCE_DAYS and (prev is None or gap < abs((prev.end - want_end).days)):
                prev = q
        if prev is None:
            return None
        chain.insert(0, prev)
    return chain


def year_ago(quarters: dict[date, Quarter], end: date) -> Quarter | None:
    target = end - timedelta(days=364)
    best = None
    for e, q in quarters.items():
        gap = abs((e - target).days)
        if gap <= YEAR_AGO_TOLERANCE_DAYS and (best is None or gap < abs((best.end - target).days)):
            best = q
    return best


def ttm(quarters: dict[date, Quarter], end: date) -> float | None:
    chain = contiguous_chain(quarters, end, 4)
    return None if chain is None else sum(q.val for q in chain)


def yoy(quarters: dict[date, Quarter], end: date) -> float | None:
    cur = quarters.get(end)
    prev = year_ago(quarters, end)
    if cur is None or prev is None or prev.val <= 0:
        return None
    return cur.val / prev.val - 1.0


# ---------------------------------------------------------------------------
# Gates
# ---------------------------------------------------------------------------

PASS, FAIL, NA = "pass", "fail", "insufficient"


@dataclass
class GateResult:
    status: str
    value: float | None = None
    detail: str = ""


@dataclass
class ScreenInput:
    revenue: dict[date, Quarter]
    op_income: dict[date, Quarter]
    gross_profit: dict[date, Quarter]
    ocf: dict[date, Quarter]
    diluted_q: dict[date, Quarter]
    diluted_fy: dict[date, Quarter]
    impairment: dict[date, Quarter] = field(default_factory=dict)
    acquisitions: dict[date, Quarter] = field(default_factory=dict)


def prior_end(quarters: dict[date, Quarter], end: date, k: int) -> date | None:
    chain = contiguous_chain(quarters, end, k + 1)
    return None if chain is None else chain[0].end


def gate_revenue_quarters(rev: dict[date, Quarter], min_q: int) -> GateResult:
    if not rev:
        return GateResult(NA, 0, "沒有營收資料")
    last = max(rev)
    longest = 0
    for n in range(1, 13):
        if contiguous_chain(rev, last, n) is None:
            break
        longest = n
    if longest >= min_q:
        return GateResult(PASS, longest, f"最新一季止連續 {longest} 季")
    if len(rev) >= min_q:
        # enough history overall, but a gap or a basis change breaks the chain: not a new listing
        return GateResult(NA, longest, f"最新一季止只連續 {longest} 季（期間不連續或口徑變動）")
    return GateResult(FAIL, longest, f"最新一季止連續 {longest} 季")


def gate_ttm_growth(rev, last, threshold) -> GateResult:
    yago = year_ago(rev, last)
    cur = ttm(rev, last)
    prev = ttm(rev, yago.end) if yago else None
    if cur is None or prev is None or prev <= 0:
        return GateResult(NA, None, "TTM 需要連續 8 季")
    g = cur / prev - 1.0
    return GateResult(PASS if g >= threshold else FAIL, g)


def gate_acceleration(rev, last, min_pp) -> GateResult:
    chain = contiguous_chain(rev, last, 3)
    if chain is None:
        return GateResult(NA, None, "需要連續 3 季與各自去年同季")
    growths = [yoy(rev, q.end) for q in chain]
    if any(g is None for g in growths):
        return GateResult(NA, None, "缺去年同季或基期為負")
    accel_pp = (growths[2] - (growths[0] + growths[1]) / 2.0) * 100
    detail = " → ".join(f"{g * 100:+.1f}%" for g in growths)
    return GateResult(PASS if accel_pp >= min_pp else FAIL, accel_pp, detail)


def ttm_margin(numer, denom, end) -> float | None:
    n, d = ttm(numer, end), ttm(denom, end)
    if n is None or d is None or d <= 0:
        return None
    return n / d


def gate_profit_inflection(rev, opi, last, min_pp) -> GateResult:
    yago = year_ago(rev, last)
    if yago is None:
        return GateResult(NA, None, "缺去年同季")
    m_now, m_prev = ttm_margin(opi, rev, last), ttm_margin(opi, rev, yago.end)
    oi_now, oi_prev = ttm(opi, last), ttm(opi, yago.end)
    if m_now is None or m_prev is None:
        return GateResult(NA, None, "營業利益或營收不足 8 季")
    change_pp = (m_now - m_prev) * 100
    turned = oi_now > 0 and oi_prev <= 0
    ok = change_pp >= min_pp or turned
    detail = f"TTM 營益率 {m_prev * 100:.1f}% → {m_now * 100:.1f}%" + ("（由虧轉盈）" if turned else "")
    return GateResult(PASS if ok else FAIL, change_pp, detail)


def gate_cash_flow(ocf, rev, last) -> GateResult:
    yago = year_ago(rev, last)
    if yago is None:
        return GateResult(NA, None, "缺去年同季")
    now, prev = ttm(ocf, last), ttm(ocf, yago.end)
    if now is None or prev is None:
        return GateResult(NA, None, "營業現金流不足 8 季")
    ok = now > prev or (now > 0 and prev <= 0)
    return GateResult(PASS if ok else FAIL, now - prev, f"TTM 營業現金流 {prev / 1e6:,.0f}M → {now / 1e6:,.0f}M")


def gate_dilution(sin: ScreenInput, last: date, max_growth: float) -> GateResult:
    q = sin.diluted_q
    if last in q:
        prev = year_ago(q, last)
        if prev and prev.val > 0:
            g = q[last].val / prev.val - 1.0
            return GateResult(PASS if g <= max_growth else FAIL, g, "單季稀釋加權股數 vs 去年同季")
    fy = sin.diluted_fy
    if last in fy:
        prev = year_ago(fy, last)
        if prev and prev.val > 0:
            g = fy[last].val / prev.val - 1.0
            return GateResult(PASS if g <= max_growth else FAIL, g, "年度稀釋加權股數 vs 前一年度")
    return GateResult(NA, None, "缺稀釋加權股數")


def annual_from_periods(periods: dict) -> dict[date, Quarter]:
    out: dict[date, Quarter] = {}
    for (s, e), entry in periods.items():
        if s is None:
            continue
        sd, ed = parse_date(s), parse_date(e)
        if in_range(days(sd, ed), ANNUAL_DAYS):
            out[ed] = Quarter(sd, ed, float(entry["val"]), False, entry.get("filed", ""))
    return out


def classify_source(gm_change_pp: float | None, sync_share: float | None, cfg: dict) -> tuple[str, str, str]:
    if gm_change_pp is None:
        vertical = "資料不足"
    elif gm_change_pp >= cfg["gross_margin_price_driven_min_pp"]:
        vertical = "報價驅動"
    elif gm_change_pp < cfg["gross_margin_volume_driven_max_pp"]:
        vertical = "銷量驅動"
    else:
        vertical = "混合"
    if sync_share is None:
        horizontal = "同業不足"
    elif sync_share >= cfg["industry_sync_share_min"]:
        horizontal = "產業同步"
    else:
        horizontal = "公司特有"
    quadrant = {
        ("銷量驅動", "公司特有"): "成長拐點",
        ("報價驅動", "公司特有"): "定價權／產品組合升級",
        ("報價驅動", "產業同步"): "循環拐點",
        ("銷量驅動", "產業同步"): "產業需求浪潮",
    }.get((vertical, horizontal), f"{vertical}／{horizontal}")
    return vertical, horizontal, quadrant


def next_quarter_requirement(rev: dict[date, Quarter], last: date, threshold: float) -> dict | None:
    """Revenue the next quarter needs for TTM growth to stay at or above the threshold."""
    chain = contiguous_chain(rev, last, 7)
    if chain is None:
        return None
    # chain: t-6 .. t ; next TTM = t-2,t-1,t,next ; prior TTM = t-6..t-3
    prior_ttm_next = sum(q.val for q in chain[0:4])
    known = sum(q.val for q in chain[4:7])
    need = (1.0 + threshold) * prior_ttm_next - known
    base = chain[3].val  # same quarter last year for the next quarter
    return {
        "next_quarter_end_approx": (last + timedelta(days=91)).isoformat(),
        "revenue_needed": need,
        "yoy_needed": (need / base - 1.0) if base > 0 else None,
    }


def utc(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))
