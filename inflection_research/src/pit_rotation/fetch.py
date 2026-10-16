"""Rate-limited, cached downloads with an append-only provenance log.

Every response body is stored gzipped under the cache directory and its
SHA-256 is appended to ``fetch_log.jsonl``. Existing cache files are never
re-downloaded or overwritten, so a rerun reads exactly the same bytes.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

SEC_USER_AGENT = os.environ.get("SEC_USER_AGENT", "inflection-research kmes4315@gmail.com")
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


class RateLimiter:
    def __init__(self, per_second: float):
        self.interval = 1.0 / per_second
        self.lock = threading.Lock()
        self.next_time = 0.0

    def wait(self):
        with self.lock:
            now = time.monotonic()
            if now < self.next_time:
                time.sleep(self.next_time - now)
                now = time.monotonic()
            self.next_time = now + self.interval


class CachedFetcher:
    def __init__(self, cache_dir: Path, user_agent: str, per_second: float):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.limiter = RateLimiter(per_second)
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"})
        self.log_path = self.cache_dir / "fetch_log.jsonl"
        self.log_lock = threading.Lock()

    def path_for(self, key: str) -> Path:
        return self.cache_dir / f"{key}.gz"

    def get(self, url: str, key: str, max_tries: int = 6) -> bytes | None:
        """Return the body for ``url``; ``None`` when the server says 404."""
        path = self.path_for(key)
        if path.exists():
            return gzip.decompress(path.read_bytes())
        if (self.cache_dir / f"{key}.404").exists():
            return None
        delay = 2.0
        for attempt in range(max_tries):
            self.limiter.wait()
            try:
                resp = self.session.get(url, timeout=60)
            except requests.RequestException:
                time.sleep(delay)
                delay *= 2
                continue
            if resp.status_code == 200:
                body = resp.content
                path.parent.mkdir(parents=True, exist_ok=True)
                tmp = path.with_suffix(".tmp")
                tmp.write_bytes(gzip.compress(body))
                tmp.rename(path)
                self._log(url, key, resp.status_code, body)
                return body
            if resp.status_code == 404:
                (self.cache_dir / f"{key}.404").parent.mkdir(parents=True, exist_ok=True)
                (self.cache_dir / f"{key}.404").write_text("")
                self._log(url, key, 404, b"")
                return None
            if resp.status_code in (403, 429, 500, 502, 503, 504):
                time.sleep(delay)
                delay = min(delay * 2, 120)
                continue
            raise RuntimeError(f"{url} -> HTTP {resp.status_code}")
        raise RuntimeError(f"{url} failed after {max_tries} tries")

    def _log(self, url: str, key: str, status: int, body: bytes):
        rec = {
            "url": url,
            "key": key,
            "status": status,
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
            "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        with self.log_lock:
            with open(self.log_path, "a") as f:
                f.write(json.dumps(rec) + "\n")
