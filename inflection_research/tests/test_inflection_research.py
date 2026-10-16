"""Acceptance tests for the v1 inflection research (stage 1)."""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pit_rotation import inflection as inf  # noqa: E402
from pit_rotation import records  # noqa: E402
from pit_rotation import universe as uni  # noqa: E402

DT = datetime(2026, 10, 16, 14, 30, tzinfo=timezone.utc)


def fact(start, end, val, filed, accn="a"):
    return {"start": start, "end": end, "val": val, "filed": filed, "accn": accn}


def quarters_from(vals, first_start=date(2024, 1, 1)):
    """Calendar quarters starting at first_start with the given values."""
    out = {}
    starts = []
    y, m = first_start.year, first_start.month
    for _ in vals:
        starts.append(date(y, m, 1))
        m += 3
        if m > 12:
            m -= 12
            y += 1
    for i, v in enumerate(vals):
        s = starts[i]
        e = (starts[i + 1] if i + 1 < len(starts) else date(s.year + (s.month + 3 > 12), (s.month + 2) % 12 + 1, 1))
        e = date.fromordinal(e.toordinal() - 1)
        out[e] = inf.Quarter(s, e, float(v))
    return out


# 1. Filings accepted after the decision time are rejected (by SEC acceptance time).
def test_rejects_filings_after_decision_time():
    accepts = {"same_day_late": datetime(2026, 10, 16, 20, 0, tzinfo=timezone.utc),
               "same_day_early": datetime(2026, 10, 16, 12, 0, tzinfo=timezone.utc)}
    assert inf.is_available(fact("2026-04-01", "2026-06-30", 1, "2026-10-15"), DT, accepts)
    assert not inf.is_available(fact("2026-04-01", "2026-06-30", 1, "2026-10-17"), DT, accepts)
    assert not inf.is_available(fact("2026-04-01", "2026-06-30", 1, "2026-10-16", "same_day_late"), DT, accepts)
    assert inf.is_available(fact("2026-04-01", "2026-06-30", 1, "2026-10-16", "same_day_early"), DT, accepts)
    # same-day filing without an acceptance timestamp is not trusted
    assert not inf.is_available(fact("2026-04-01", "2026-06-30", 1, "2026-10-16", "unknown"), DT, accepts)


# 2. Adding or restating data after the decision time does not change the past list.
def test_later_filings_do_not_change_past_view():
    base = [fact("2026-04-01", "2026-06-30", 100, "2026-08-01", "x1")]
    later = base + [fact("2026-04-01", "2026-06-30", 120, "2026-11-01", "x2")]
    a = inf.latest_by_period(base, DT)
    b = inf.latest_by_period(later, DT)
    assert a == b
    # a restatement filed before the decision time does apply from its filing time on
    restated = base + [fact("2026-04-01", "2026-06-30", 110, "2026-09-01", "x3")]
    assert inf.latest_by_period(restated, DT)[("2026-04-01", "2026-06-30")]["val"] == 110


# 3. TTM and Q4 derivation; mismatched periods stay blank.
def test_q4_derived_from_annual_minus_nine_months():
    periods = {
        ("2025-01-01", "2025-03-31"): {"val": 10, "filed": "2025-05-01"},
        ("2025-01-01", "2025-06-30"): {"val": 22, "filed": "2025-08-01"},
        ("2025-01-01", "2025-09-30"): {"val": 36, "filed": "2025-11-01"},
        ("2025-01-01", "2025-12-31"): {"val": 52, "filed": "2026-02-20"},
    }
    q = inf.quarterly_from_periods(periods)
    assert [q[d].val for d in sorted(q)] == [10, 12, 14, 16]
    assert q[date(2025, 12, 31)].derived
    assert inf.ttm(q, date(2025, 12, 31)) == 52


def test_q4_from_annual_minus_three_direct_quarters():
    periods = {
        ("2025-01-01", "2025-03-31"): {"val": 10},
        ("2025-04-01", "2025-06-30"): {"val": 12},
        ("2025-07-01", "2025-09-30"): {"val": 14},
        ("2025-01-01", "2025-12-31"): {"val": 52},
    }
    q = inf.quarterly_from_periods(periods)
    assert q[date(2025, 12, 31)].val == 16


def test_gap_leaves_ttm_blank():
    periods = {
        ("2025-01-01", "2025-03-31"): {"val": 10},
        ("2025-07-01", "2025-09-30"): {"val": 14},
        ("2025-10-01", "2025-12-31"): {"val": 16},
        ("2026-01-01", "2026-03-31"): {"val": 18},
    }
    q = inf.quarterly_from_periods(periods)
    assert inf.ttm(q, date(2026, 3, 31)) is None
    g = inf.gate_ttm_growth(q, date(2026, 3, 31), 0.2)
    assert g.status == inf.NA


def test_inconsistent_concepts_are_not_mixed():
    a = {("2025-01-01", "2025-03-31"): {"val": 100}, ("2025-04-01", "2025-06-30"): {"val": 110}}
    b = {("2025-04-01", "2025-06-30"): {"val": 80}, ("2024-10-01", "2024-12-31"): {"val": 70}}
    merged, used = inf.merge_concepts({"A": a, "B": b}, ["A", "B"])
    assert used == ["A"] and ("2024-10-01", "2024-12-31") not in merged
    c = {("2025-04-01", "2025-06-30"): {"val": 110}, ("2024-10-01", "2024-12-31"): {"val": 95}}
    merged, used = inf.merge_concepts({"A": a, "C": c}, ["A", "C"])
    assert used == ["A", "C"] and merged[("2024-10-01", "2024-12-31")]["val"] == 95


# 4. Dilution uses split-adjusted comparatives (latest filed version of the year-ago quarter).
def test_dilution_uses_restated_comparative_after_split():
    entries = [
        fact("2025-04-01", "2025-06-30", 100, "2025-08-01", "old"),      # pre-split original
        fact("2025-04-01", "2025-06-30", 1000, "2026-08-01", "new"),     # comparative restated 10:1
        fact("2026-04-01", "2026-06-30", 1050, "2026-08-01", "new"),
    ]
    per = inf.latest_by_period(entries, DT)
    sin = inf.ScreenInput({}, {}, {}, {}, inf.quarterly_from_periods(per, additive=False), {})
    g = inf.gate_dilution(sin, date(2026, 6, 30), 0.08)
    assert g.status == inf.PASS and abs(g.value - 0.05) < 1e-9


# 5. Missing data stays missing and never counts as a pass.
def test_missing_data_is_not_a_pass():
    rev = quarters_from([100, 110, 120, 130, 140, 150, 170, 200])
    last = max(rev)
    assert inf.gate_profit_inflection(rev, {}, last, 5).status == inf.NA
    assert inf.gate_cash_flow({}, rev, last).status == inf.NA
    sin = inf.ScreenInput(rev, {}, {}, {}, {}, {})
    assert inf.gate_dilution(sin, last, 0.08).status == inf.NA


def test_acceleration_and_growth_math():
    # yoy for last three quarters: 140/100-1=40%, 150/110-1=36.4%, 200/130-1=53.8%... use explicit values
    rev = quarters_from([100, 100, 100, 100, 120, 125, 130, 160])
    last = max(rev)
    g3 = inf.gate_acceleration(rev, last, 5)
    # yoys: 25%, 30%, 60% -> 60 - 27.5 = 32.5pp
    assert g3.status == inf.PASS and abs(g3.value - 32.5) < 1e-9
    g2 = inf.gate_ttm_growth(rev, last, 0.2)
    assert abs(g2.value - (535 / 400 - 1)) < 1e-12


# 6. Source classification and thesis state follow the rules; a price drop alone changes nothing.
def test_source_classification():
    cfg = {"gross_margin_price_driven_min_pp": 10, "gross_margin_volume_driven_max_pp": 5, "industry_sync_share_min": 0.5}
    assert inf.classify_source(1.0, 0.2, cfg)[2] == "成長拐點"
    assert inf.classify_source(15.0, 0.8, cfg)[2] == "循環拐點"
    assert inf.classify_source(12.0, 0.1, cfg)[2] == "定價權／產品組合升級"
    assert inf.classify_source(2.0, 0.9, cfg)[2] == "產業需求浪潮"
    assert inf.classify_source(7.0, 0.9, cfg)[0] == "混合"
    assert inf.classify_source(None, None, cfg)[:2] == ("資料不足", "同業不足")


def test_gates_ignore_price():
    import inspect

    for fn in (inf.gate_ttm_growth, inf.gate_acceleration, inf.gate_profit_inflection, inf.gate_cash_flow,
               inf.gate_dilution, inf.classify_source):
        params = inspect.signature(fn).parameters
        assert not any("price" in p for p in params), fn.__name__


# 7. Records are append-only; editing an old record is detected.
def test_records_append_only(tmp_path):
    records.write_period(tmp_path, "2026-10-16", {"a.csv": b"x\n"}, {"decision_time_utc": "t"})
    with pytest.raises(FileExistsError):
        records.write_period(tmp_path, "2026-10-16", {"a.csv": b"y\n"}, {})
    records.write_period(tmp_path, "2026-10-23", {"a.csv": b"z\n"}, {})
    assert len(records.verify_ledger(tmp_path)) == 2
    (tmp_path / "2026-10-16" / "a.csv").write_bytes(b"edited\n")
    with pytest.raises(records.RecordTampered):
        records.verify_ledger(tmp_path)
    with pytest.raises(records.RecordTampered):
        records.write_period(tmp_path, "2026-10-30", {"a.csv": b"w\n"}, {})


# 8. The universe snapshot keeps every company in the cap band, including excluded ones.
def test_snapshot_keeps_excluded_companies():
    src = (ROOT / "scripts/run_inflection_snapshot_v1.py").read_text()
    assert "universe_rows.append(row)" in src
    # rows are appended before the screening decision, so exclusions stay in the snapshot
    assert src.index("universe_rows.append(row)") < src.index('if scope == "篩選":')


# 9. The research code never reads holdings or portfolio files.
def test_no_holdings_access():
    for p in list((ROOT / "src").rglob("*.py")) + list((ROOT / "scripts").glob("*.py")):
        text = p.read_text().lower()
        for word in ("holdings.csv", "holdings_", "portfolio", "positions.csv", "broker"):
            assert word not in text, f"{p.name} mentions {word}"


# 10. Same input, same output.
def test_deterministic_rerun():
    periods = {
        ("2025-01-01", "2025-03-31"): {"val": 10},
        ("2025-01-01", "2025-06-30"): {"val": 22},
        ("2025-01-01", "2025-09-30"): {"val": 36},
        ("2025-01-01", "2025-12-31"): {"val": 52},
    }
    a = inf.quarterly_from_periods(dict(periods))
    b = inf.quarterly_from_periods(dict(reversed(list(periods.items()))))
    assert {k: v.val for k, v in a.items()} == {k: v.val for k, v in b.items()}


def test_primary_ticker_skips_warrants_and_otc():
    sub = {"tickers": ["ABCDW", "ABCD", "ABCD-PA"], "exchanges": ["Nasdaq", "Nasdaq", "NYSE"]}
    assert uni.primary_ticker(sub, {"Nasdaq", "NYSE"}) == ("ABCD", "Nasdaq")
    assert uni.primary_ticker({"tickers": ["XYZ"], "exchanges": ["OTC"]}, {"Nasdaq"}) is None


def test_next_quarter_requirement():
    rev = quarters_from([100, 100, 100, 100, 120, 125, 130, 160])
    req = inf.next_quarter_requirement(rev, max(rev), 0.20)
    # next TTM = 125+130+160+x ; prior = 100+120?? -> chain t-6..t-3 = 100,100,100,120 = 420 ; need 1.2*420 - 415 = 89
    assert abs(req["revenue_needed"] - (1.2 * 420 - 415)) < 1e-9


def test_fsds_supplement_only_fills_missing_filings():
    from pit_rotation import fsds

    assert fsds._start_for("2026-06-30", 1) == "2026-04-01"
    assert fsds._start_for("2026-06-30", 2) == "2026-01-01"
    facts = {"facts": {"us-gaap": {"Revenues": {"units": {"USD": [
        {"start": "2026-01-04", "end": "2026-04-04", "val": 10, "accn": "a1", "filed": "2026-05-01"}]}}}}}
    extra = {("us-gaap", "Revenues", "USD"): [
        {"start": "2026-01-01", "end": "2026-07-04", "val": 22, "accn": "a2", "filed": "2026-08-01"},
        {"start": "2026-01-01", "end": "2026-04-04", "val": 99, "accn": "a1", "filed": "2026-05-01"}]}
    merged, n = fsds.supplement(facts, extra)
    entries = merged["facts"]["us-gaap"]["Revenues"]["units"]["USD"]
    assert n == 1 and len(entries) == 2
    # start snapped to the company's own fiscal start so 6M - 3M still derives Q2
    assert entries[1]["start"] == "2026-01-04"
    q = inf.quarterly_from_periods({(e["start"], e["end"]): e for e in entries})
    assert q[date(2026, 7, 4)].val == 12
