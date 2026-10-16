"""Append-only period records with a SHA-256 hash chain.

Each period is written once into its own directory together with a manifest
listing every file's SHA-256. ``ledger.jsonl`` chains the manifests: each line
stores the previous line's hash. Before anything new is written the whole
ledger is re-verified; an edited old file or ledger line stops the program.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


class RecordTampered(RuntimeError):
    pass


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    return sha256_bytes(Path(p).read_bytes())


def verify_ledger(root: Path) -> list[dict]:
    root = Path(root)
    ledger = root / "ledger.jsonl"
    if not ledger.exists():
        return []
    entries = []
    prev = "0" * 64
    for i, line in enumerate(ledger.read_text().splitlines()):
        rec = json.loads(line)
        if rec["prev_hash"] != prev:
            raise RecordTampered(f"ledger line {i}: chain broken")
        body = {k: v for k, v in rec.items() if k != "hash"}
        if sha256_bytes(json.dumps(body, sort_keys=True).encode()) != rec["hash"]:
            raise RecordTampered(f"ledger line {i}: line edited")
        manifest_path = root / rec["period"] / "manifest.json"
        if sha256_file(manifest_path) != rec["manifest_sha256"]:
            raise RecordTampered(f"{rec['period']}: manifest edited")
        manifest = json.loads(manifest_path.read_text())
        for name, digest in manifest["files"].items():
            if sha256_file(root / rec["period"] / name) != digest:
                raise RecordTampered(f"{rec['period']}/{name}: file edited")
        entries.append(rec)
        prev = rec["hash"]
    return entries


def write_period(root: Path, period: str, files: dict[str, bytes], meta: dict) -> dict:
    root = Path(root)
    entries = verify_ledger(root)
    if any(e["period"] == period for e in entries) or (root / period).exists():
        raise FileExistsError(f"period {period} already recorded; records are append-only")
    pdir = root / period
    pdir.mkdir(parents=True)
    hashes = {}
    for name in sorted(files):
        (pdir / name).write_bytes(files[name])
        hashes[name] = sha256_bytes(files[name])
    manifest = {"period": period, **meta, "files": hashes}
    mbytes = json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False).encode()
    (pdir / "manifest.json").write_bytes(mbytes)
    body = {
        "period": period,
        "manifest_sha256": sha256_bytes(mbytes),
        "prev_hash": entries[-1]["hash"] if entries else "0" * 64,
    }
    body["hash"] = sha256_bytes(json.dumps(body, sort_keys=True).encode())
    with open(root / "ledger.jsonl", "a") as f:
        f.write(json.dumps(body, sort_keys=True) + "\n")
    return manifest
