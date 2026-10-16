"""Supplement XBRL companyfacts with SEC Financial Statement Data Sets.

The companyfacts API sometimes lacks a recent 10-Q/10-K. The quarterly
Financial Statement Data Sets (sub.txt + num.txt) carry the same tagged values
with filing dates, so for any filing missing from companyfacts we add its
non-dimensional facts in companyfacts' entry format.

FSDS rounds period ends to the nearest month end and gives only the length in
quarters, so start and end dates are reconstructed and then snapped to dates
the company already uses (within 7 days) so periods line up with companyfacts.
"""

from __future__ import annotations

import csv
import io
import zipfile
from datetime import date, timedelta

SNAP_DAYS = 7


def _iso(yyyymmdd: str) -> str:
    return f"{yyyymmdd[0:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:8]}"


def _start_for(end_iso: str, qtrs: int) -> str:
    end = date.fromisoformat(end_iso)
    nxt = end + timedelta(days=1)
    m = nxt.month - 3 * qtrs
    y = nxt.year
    while m <= 0:
        m += 12
        y -= 1
    day = min(nxt.day, 28)
    return date(y, m, day).isoformat()


def load_fsds(zip_bytes: bytes, tags: set[str], forms=("10-Q", "10-K", "10-Q/A", "10-K/A")) -> dict:
    """Return {cik: {(taxonomy, tag, unit): [entry, ...]}} for the listed tags."""
    z = zipfile.ZipFile(io.BytesIO(zip_bytes))
    subs = {}
    with z.open("sub.txt") as f:
        for row in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8", errors="ignore"), delimiter="\t"):
            if row["form"] in forms:
                subs[row["adsh"]] = (int(row["cik"]), row["form"], _iso(row["filed"]))
    out: dict = {}
    with z.open("num.txt") as f:
        reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8", errors="ignore"), delimiter="\t")
        for row in reader:
            if row["tag"] not in tags or row.get("segments") or row.get("coreg"):
                continue
            sub = subs.get(row["adsh"])
            if sub is None or not row["value"]:
                continue
            taxonomy = row["version"].split("/")[0]
            if taxonomy not in ("us-gaap", "dei"):
                continue
            cik, form, filed = sub
            end = _iso(row["ddate"])
            qtrs = int(row["qtrs"])
            entry = {"end": end, "val": float(row["value"]), "accn": row["adsh"], "form": form, "filed": filed,
                     "source": "fsds"}
            if qtrs > 0:
                entry["start"] = _start_for(end, qtrs)
            out.setdefault(cik, {}).setdefault((taxonomy, row["tag"], row["uom"]), []).append(entry)
    return out


def supplement(facts: dict | None, extra: dict | None) -> tuple[dict | None, int]:
    """Add FSDS entries for filings the companyfacts document does not contain."""
    if not extra:
        return facts, 0
    facts = facts or {"facts": {}}
    known_accn, known_starts, known_ends = set(), set(), set()
    for tax in facts.get("facts", {}).values():
        for concept in tax.values():
            for entries in concept.get("units", {}).values():
                for e in entries:
                    known_accn.add(e.get("accn"))
                    known_ends.add(e["end"])
                    if e.get("start"):
                        known_starts.add(e["start"])
    starts = sorted(date.fromisoformat(s) for s in known_starts)
    ends = sorted(date.fromisoformat(s) for s in known_ends)

    def snap(value: str, pool: list[date]) -> str:
        d = date.fromisoformat(value)
        near = [k for k in pool if abs((k - d).days) <= SNAP_DAYS]
        return min(near, key=lambda k: abs((k - d).days)).isoformat() if near else value

    added_filings = set()
    for (taxonomy, tag, unit), entries in extra.items():
        for e in entries:
            if e["accn"] in known_accn:
                continue
            e = dict(e)
            e["end"] = snap(e["end"], ends)
            if e.get("start"):
                e["start"] = snap(e["start"], starts)
            units = facts["facts"].setdefault(taxonomy, {}).setdefault(tag, {}).setdefault("units", {})
            units.setdefault(unit, []).append(e)
            added_filings.add(e["accn"])
    return facts, len(added_filings)
