"""Cached, throttled network access for label-noise jobs.

Every call is content-addressed on disk under data/cache/labelnoise/ so
reruns are free and deterministic. Politeness: <=2 req/s per host class,
exponential backoff, identifying User-Agent for keyless APIs.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import subprocess
import time
from pathlib import Path

import httpx

from vc_brain.ingest.contracts import DATA_ROOT

LOGGER = logging.getLogger(__name__)
CACHE_ROOT = DATA_ROOT / "cache" / "labelnoise"
USER_AGENT = (
    "vc-brain-research/0.1 "
    "(contact: misha.aghamalyan@gmail.com; label-noise study)"
)
_LAST_REQUEST = {"t": 0.0}


def _throttle(min_interval: float = 0.55) -> None:
    elapsed = time.time() - _LAST_REQUEST["t"]
    if elapsed < min_interval:
        time.sleep(min_interval - elapsed)
    _LAST_REQUEST["t"] = time.time()


def _cache_path(namespace: str, key: str) -> Path:
    safe = re.sub(r"[^a-zA-Z0-9_.-]", "_", key)[:80]
    digest = hashlib.sha256(key.encode()).hexdigest()[:16]
    return CACHE_ROOT / namespace / f"{safe}_{digest}.json"


def get_json(client: httpx.Client, url: str, namespace: str, key: str):
    """GET a JSON endpoint with disk cache; 404 cached as None."""
    path = _cache_path(namespace, key)
    if path.exists():
        return json.loads(path.read_text())
    path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(5):
        _throttle()
        try:
            response = client.get(url)
            if response.status_code == 200:
                data = response.json()
                path.write_text(json.dumps(data))
                return data
            if response.status_code == 404:
                path.write_text("null")
                return None
            if response.status_code in (429, 500, 502, 503):
                time.sleep(2**attempt)
                continue
            path.write_text("null")
            return None
        except (httpx.HTTPError, json.JSONDecodeError) as error:
            LOGGER.warning("%s attempt %d: %s", url, attempt + 1, error)
            time.sleep(2**attempt)
    return None


def get_text(client: httpx.Client, url: str, namespace: str, key: str) -> str | None:
    """GET a web page (e.g. a control's blog); cache raw text, None on failure."""
    path = _cache_path(namespace, key)
    if path.exists():
        cached = json.loads(path.read_text())
        return cached["text"] if cached else None
    path.parent.mkdir(parents=True, exist_ok=True)
    _throttle()
    try:
        response = client.get(url, follow_redirects=True, timeout=20.0)
        if response.status_code == 200 and "text" in response.headers.get(
            "content-type", "text"
        ):
            text = response.text[:200_000]
            path.write_text(json.dumps({"text": text, "final_url": str(response.url)}))
            return text
    except httpx.HTTPError as error:
        LOGGER.warning("blog fetch %s failed: %s", url, error)
    path.write_text("null")
    return None


def gh_api_user(login: str) -> dict | None:
    """gh api users/<login> via the authenticated gh CLI; None on 404/GONE."""
    path = _cache_path("gh_users", login.lower())
    if path.exists():
        return json.loads(path.read_text())
    path.parent.mkdir(parents=True, exist_ok=True)
    _throttle()
    result = subprocess.run(
        ["gh", "api", f"users/{login}"], capture_output=True, text=True, timeout=60
    )
    if result.returncode == 0:
        data = json.loads(result.stdout)
        path.write_text(json.dumps(data))
        return data
    if "404" in result.stderr or "Not Found" in result.stderr:
        path.write_text("null")
        return None
    raise RuntimeError(f"gh api users/{login} failed: {result.stderr[:200]}")


def strip_html(html: str, limit: int = 3000) -> str:
    """Crude tag-stripper adequate for LLM adjudication of a landing page."""
    text = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()[:limit]
