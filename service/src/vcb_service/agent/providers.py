"""Polite cached public-data clients used by the deep-dive sandbox."""

import hashlib
import json
import random
import subprocess
import time
from pathlib import Path
from typing import Any, Protocol

import httpx


class DataProvider(Protocol):
    def close(self) -> None: ...
    def gh_profile(self, login: str) -> dict[str, Any]: ...
    def gh_repos(self, login: str) -> list[dict[str, Any]]: ...
    def gh_events(self, login: str) -> list[dict[str, Any]]: ...
    def hn_search(self, query: str) -> dict[str, Any]: ...
    def web_search(self, query: str) -> dict[str, Any]: ...


class PublicFetchError(RuntimeError):
    code = "PUBLIC_FETCH_FAILED"


class PublicDataProvider:
    """Single-threaded, disk-cached GET client with bounded exponential backoff."""

    def __init__(
        self,
        cache_dir: Path,
        *,
        serpapi_key: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.cache_dir = cache_dir
        self.serpapi_key = serpapi_key
        self._client = client or httpx.Client(timeout=12.0, follow_redirects=True)
        self._owns_client = client is None
        self._github_token: str | None | object = _UNSET

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def gh_profile(self, login: str) -> dict[str, Any]:
        return self._cached_get("gh-profile", f"https://api.github.com/users/{login}")

    def gh_repos(self, login: str) -> list[dict[str, Any]]:
        return self._cached_get(
            "gh-repos",
            f"https://api.github.com/users/{login}/repos",
            params={"per_page": 100, "sort": "updated"},
        )

    def gh_events(self, login: str) -> list[dict[str, Any]]:
        return self._cached_get(
            "gh-events",
            f"https://api.github.com/users/{login}/events/public",
            params={"per_page": 100},
        )

    def hn_search(self, query: str) -> dict[str, Any]:
        return self._cached_get(
            "hn-search",
            "https://hn.algolia.com/api/v1/search",
            params={"query": query, "tags": "story", "hitsPerPage": 30},
        )

    def web_search(self, query: str) -> dict[str, Any]:
        if not self.serpapi_key:
            return {
                "error": {
                    "code": "SERPAPI_UNAVAILABLE",
                    "message": "SERPAPI_KEY is not configured.",
                }
            }
        return self._cached_get(
            "web-search",
            "https://serpapi.com/search.json",
            params={"q": query, "api_key": self.serpapi_key, "num": 10},
            redact_params={"api_key"},
        )

    def _headers(self, url: str) -> dict[str, str]:
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "vc-brain-deepdive/1.0"}
        if "api.github.com" in url:
            token = self._get_github_token()
            if token:
                headers["Authorization"] = f"Bearer {token}"
                headers["X-GitHub-Api-Version"] = "2022-11-28"
        return headers

    def _get_github_token(self) -> str | None:
        if self._github_token is _UNSET:
            try:
                result = subprocess.run(
                    ["gh", "auth", "token"],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
                self._github_token = result.stdout.strip() or None
            except (FileNotFoundError, subprocess.SubprocessError):
                self._github_token = None
        return self._github_token if isinstance(self._github_token, str) else None

    def _cached_get(
        self,
        namespace: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        redact_params: set[str] | None = None,
    ) -> Any:
        safe_params = {
            key: "[redacted]" if redact_params and key in redact_params else value
            for key, value in (params or {}).items()
        }
        key = hashlib.sha256(
            json.dumps([url, safe_params], sort_keys=True).encode("utf-8")
        ).hexdigest()[:24]
        path = self.cache_dir / namespace / f"{key}.json"
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = self._client.get(url, params=params, headers=self._headers(url))
                response.raise_for_status()
                payload = response.json()
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
                return payload
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc
                if attempt < 2:
                    time.sleep((0.25 * (2**attempt)) + random.uniform(0.0, 0.05))
        raise PublicFetchError(
            f"public fetch failed after 3 attempts: {namespace}"
        ) from last_error


class FixtureProvider:
    """Recorded fixture provider; it never creates an HTTP client or uses network."""

    def __init__(self, fixture_path: Path) -> None:
        self.payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        self.serpapi_key = None

    def close(self) -> None:
        return None

    def gh_profile(self, login: str) -> dict[str, Any]:
        return self.payload["gh_profile"]

    def gh_repos(self, login: str) -> list[dict[str, Any]]:
        return self.payload["gh_repos"]

    def gh_events(self, login: str) -> list[dict[str, Any]]:
        return self.payload["gh_events"]

    def hn_search(self, query: str) -> dict[str, Any]:
        return self.payload["hn_search"]

    def web_search(self, query: str) -> dict[str, Any]:
        return self.payload["web_search"]


_UNSET = object()
