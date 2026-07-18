"""Stage 3: resolve YC founders to high-confidence GitHub identities."""

import json
import logging
import os
import re
import subprocess
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import httpx
import polars as pl
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt
from tenacity import wait_random_exponential

from vc_brain.labels.contracts import (
    FOUNDERS_RAW_PATH,
    FOUNDERS_RESOLVED_PATH,
    RESOLUTION_SCHEMA,
)
from vc_brain.labels.identity import (
    normalize_domain,
    normalize_text,
    twitter_handle,
)
from vc_brain.labels.storage import (
    atomic_write_json,
    atomic_write_parquet,
    checkpoint_path,
    frame_from_rows,
    read_checkpoint,
)
from vc_brain.labels.yc_companies import USER_AGENT

LOGGER = logging.getLogger(__name__)
GITHUB_API_ROOT = "https://api.github.com"
SERPAPI_URL = "https://serpapi.com/search.json"
CHECKPOINT_INTERVAL = 50
PROGRESS_INTERVAL = 50
SEARCH_LIMIT_PER_MINUTE = 30
MIN_CONFIDENCE = 0.5
RESERVED_GITHUB_PATHS = {
    "about",
    "apps",
    "collections",
    "contact",
    "customer-stories",
    "enterprise",
    "events",
    "features",
    "issues",
    "login",
    "marketplace",
    "new",
    "notifications",
    "orgs",
    "pricing",
    "pulls",
    "search",
    "security",
    "settings",
    "signup",
    "sponsors",
    "topics",
    "trending",
}


class RetryableAPIError(RuntimeError):
    """A transient GitHub or SerpAPI failure."""


class APIRequestError(RuntimeError):
    """A permanent external API failure with a safe diagnostic."""


class GitHubCredentialsUnavailableError(RuntimeError):
    """No usable GitHub CLI credential is configured."""


class InvalidSerpAPIConfigurationError(RuntimeError):
    """SERPAPI_CAP is not a valid non-negative integer."""


def name_token_similarity(left: str | None, right: str | None) -> float:
    left_tokens = sorted(set(normalize_text(left).split()))
    right_tokens = sorted(set(normalize_text(right).split()))
    if not left_tokens or not right_tokens:
        return 0.0
    return SequenceMatcher(None, " ".join(left_tokens), " ".join(right_tokens)).ratio()


def score_candidate(
    candidate: dict[str, Any],
    founder: dict[str, Any],
    *,
    candidate_count: int,
) -> tuple[float, dict[str, Any]]:
    """Apply the verified additive identity confidence formula."""
    score = 0.0
    signals: dict[str, Any] = {}

    yc_twitter = twitter_handle(founder.get("twitter_url"))
    github_twitter = twitter_handle(candidate.get("twitter_username"))
    if yc_twitter and github_twitter and yc_twitter == github_twitter:
        score += 0.50
        signals["twitter_match"] = True

    company_domain = normalize_domain(founder.get("company_website"))
    github_domain = normalize_domain(candidate.get("blog"))
    if company_domain and github_domain and company_domain == github_domain:
        score += 0.40
        signals["website_domain_match"] = company_domain

    company_name = normalize_text(founder.get("company"))
    candidate_affiliation = normalize_text(
        " ".join(
            str(candidate.get(field) or "") for field in ("bio", "company")
        )
    )
    if company_name and company_name in candidate_affiliation:
        score += 0.30
        signals["company_name_match"] = True

    similarity = name_token_similarity(founder.get("founder_name"), candidate.get("name"))
    if similarity >= 0.9:
        score += 0.20
        signals["name_token_similarity"] = round(similarity, 4)

    if candidate_count == 1:
        score += 0.10
        signals["single_search_candidate"] = True

    login = str(candidate.get("login") or "")
    if "bot" in login.lower() or candidate.get("type") != "User":
        score -= 0.30
        signals["bot_or_non_user_penalty"] = True

    return min(1.0, max(0.0, score)), signals


def read_github_tokens() -> list[str]:
    """Read configured GitHub CLI tokens once, without exposing their values."""
    commands = (
        ["gh", "auth", "token"],
        ["gh", "auth", "token", "--user", "misha-supertruth"],
    )
    tokens: list[str] = []
    for command in commands:
        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (FileNotFoundError, subprocess.SubprocessError):
            continue
        token = result.stdout.strip()
        if token and token not in tokens:
            tokens.append(token)
    if not tokens:
        raise GitHubCredentialsUnavailableError(
            "No GitHub CLI token available; authenticate with `gh auth login`"
        )
    LOGGER.info("Loaded GitHub credentials token_count=%d", len(tokens))
    return tokens


@dataclass
class TokenState:
    token: str
    search_calls: deque[float] = field(default_factory=deque)
    search_remaining: int | None = None
    core_remaining: int | None = None
    reset_at: float = 0.0


class GitHubRateLimitPool:
    """Explicit token rotation and GitHub rate-limit accounting."""

    def __init__(self, tokens: list[str]) -> None:
        if not tokens:
            raise ValueError("At least one GitHub token is required")
        self.states = [TokenState(token) for token in tokens]
        self.next_index = 0

    def acquire(self, resource: str) -> TokenState:
        while True:
            now = time.time()
            waits: list[float] = []
            for offset in range(len(self.states)):
                index = (self.next_index + offset) % len(self.states)
                state = self.states[index]
                if resource == "search":
                    while state.search_calls and now - state.search_calls[0] >= 60:
                        state.search_calls.popleft()
                    locally_available = len(state.search_calls) < SEARCH_LIMIT_PER_MINUTE
                    remotely_available = (
                        state.search_remaining is None
                        or state.search_remaining >= 2
                        or now >= state.reset_at
                    )
                    if locally_available and remotely_available:
                        state.search_calls.append(now)
                        self.next_index = (index + 1) % len(self.states)
                        return state
                    if state.search_calls:
                        waits.append(max(0.0, 60 - (now - state.search_calls[0])))
                else:
                    if (
                        state.core_remaining is None
                        or state.core_remaining >= 2
                        or now >= state.reset_at
                    ):
                        self.next_index = (index + 1) % len(self.states)
                        return state
                if state.reset_at > now:
                    waits.append(state.reset_at - now)
            delay = max(0.25, min(waits, default=60.0))
            LOGGER.info(
                "GitHub rate limit waiting resource=%s seconds=%.1f",
                resource,
                delay,
            )
            time.sleep(delay)

    @staticmethod
    def record_response(state: TokenState, response: httpx.Response) -> None:
        remaining = response.headers.get("X-RateLimit-Remaining")
        reset = response.headers.get("X-RateLimit-Reset")
        resource = response.headers.get("X-RateLimit-Resource", "core")
        if remaining and remaining.isdigit():
            if resource == "search":
                state.search_remaining = int(remaining)
            else:
                state.core_remaining = int(remaining)
        if reset and reset.isdigit():
            state.reset_at = float(reset) + 1.0


class GitHubClient:
    """GitHub request execution composed with explicit token scheduling."""

    def __init__(
        self,
        tokens: list[str],
        client: httpx.Client | None = None,
        rate_limits: GitHubRateLimitPool | None = None,
    ) -> None:
        self.rate_limits = rate_limits or GitHubRateLimitPool(tokens)
        self.owns_client = client is None
        self.client = client or httpx.Client(
            base_url=GITHUB_API_ROOT,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": USER_AGENT,
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=httpx.Timeout(30.0),
        )

    def __enter__(self) -> "GitHubClient":
        return self

    def __exit__(self, *_args: object) -> None:
        if self.owns_client:
            self.client.close()

    def get_json(
        self, path: str, *, resource: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        for attempt in Retrying(
            retry=retry_if_exception_type((httpx.TransportError, RetryableAPIError)),
            stop=stop_after_attempt(5),
            wait=wait_random_exponential(multiplier=1, max=30),
            reraise=True,
        ):
            with attempt:
                state = self.rate_limits.acquire(resource)
                response = self.client.get(
                    path,
                    params=params,
                    headers={"Authorization": f"Bearer {state.token}"},
                )
                self.rate_limits.record_response(state, response)
                if response.status_code == 429 or response.status_code >= 500:
                    raise RetryableAPIError(
                        f"GitHub API returned HTTP {response.status_code}"
                    )
                if response.status_code == 403 and state.reset_at > time.time():
                    raise RetryableAPIError("GitHub API rate limit exhausted")
                if response.status_code >= 400:
                    raise APIRequestError(
                        f"GitHub API request failed path={path} "
                        f"status={response.status_code}"
                    )
                payload = response.json()
                if not isinstance(payload, dict):
                    raise APIRequestError(
                        f"GitHub API returned a non-object payload path={path}"
                    )
                return payload
        raise AssertionError("unreachable")

    def search_users(self, full_name: str) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        seen: set[str] = set()
        for qualifier in ("in:name", "in:fullname"):
            payload = self.get_json(
                "/search/users",
                resource="search",
                params={"q": f'"{full_name}" {qualifier}', "per_page": 8},
            )
            items = payload.get("items", [])
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                login = str(item.get("login") or "")
                if login and login.lower() not in seen:
                    seen.add(login.lower())
                    candidates.append(item)
                if len(candidates) >= 8:
                    return candidates
        return candidates

    def user(self, login: str) -> dict[str, Any]:
        return self.get_json(f"/users/{login}", resource="core")


def select_best_candidate(
    profiles: list[dict[str, Any]], founder: dict[str, Any], candidate_count: int
) -> tuple[dict[str, Any] | None, float, dict[str, Any]]:
    best_profile: dict[str, Any] | None = None
    best_score = 0.0
    best_signals: dict[str, Any] = {}
    for profile in profiles:
        score, signals = score_candidate(
            profile, founder, candidate_count=candidate_count
        )
        if best_profile is None or score > best_score:
            best_profile = profile
            best_score = score
            best_signals = signals
    return best_profile, best_score, best_signals


def github_logins_from_serp(payload: dict[str, Any]) -> list[str]:
    results = payload.get("organic_results", [])
    if not isinstance(results, list):
        return []
    logins: list[str] = []
    seen: set[str] = set()
    pattern = re.compile(r"https?://(?:www\.)?github\.com/([^/?#]+)", re.I)
    for result in results:
        if not isinstance(result, dict):
            continue
        for field_name in ("link", "displayed_link"):
            match = pattern.search(str(result.get(field_name) or ""))
            if not match:
                continue
            login = match.group(1)
            lowered = login.lower()
            if lowered not in RESERVED_GITHUB_PATHS and lowered not in seen:
                seen.add(lowered)
                logins.append(login)
    return logins[:8]


def serpapi_search(founder: dict[str, Any], api_key: str) -> list[str]:
    query = f'site:github.com "{founder["founder_name"]}" {founder["company"]}'
    with httpx.Client(
        headers={"User-Agent": USER_AGENT}, timeout=httpx.Timeout(30.0)
    ) as client:
        for attempt in Retrying(
            retry=retry_if_exception_type((httpx.TransportError, RetryableAPIError)),
            stop=stop_after_attempt(5),
            wait=wait_random_exponential(multiplier=1, max=30),
            reraise=True,
        ):
            with attempt:
                try:
                    response = client.get(
                        SERPAPI_URL,
                        params={
                            "engine": "google",
                            "q": query,
                            "api_key": api_key,
                        },
                    )
                except httpx.TransportError:
                    raise RetryableAPIError("SerpAPI transport failure") from None
                if response.status_code == 429 or response.status_code >= 500:
                    raise RetryableAPIError(
                        f"SerpAPI returned HTTP {response.status_code}"
                    )
                if response.status_code >= 400:
                    raise APIRequestError(
                        f"SerpAPI request failed status={response.status_code}"
                    )
                payload = response.json()
                if not isinstance(payload, dict):
                    raise APIRequestError("SerpAPI returned a non-object payload")
                return github_logins_from_serp(payload)
    raise AssertionError("unreachable")


def resolve_founder(
    founder: dict[str, Any],
    github: GitHubClient,
    *,
    serpapi_key: str | None,
    serpapi_cap: int,
    state: dict[str, Any],
    state_path: Path,
) -> dict[str, Any]:
    candidates = github.search_users(founder["founder_name"])
    profiles = [github.user(candidate["login"]) for candidate in candidates]
    best, score, signals = select_best_candidate(profiles, founder, len(candidates))
    method = "search"

    should_use_serpapi = (
        score < MIN_CONFIDENCE
        and founder["batch_year"] >= 2022
        and serpapi_key
        and int(state["serpapi_calls"]) < serpapi_cap
    )
    if should_use_serpapi:
        state["serpapi_calls"] = int(state["serpapi_calls"]) + 1
        atomic_write_json(state, state_path)
        serp_logins = serpapi_search(founder, serpapi_key)
        serp_profiles = [github.user(login) for login in serp_logins]
        serp_best, serp_score, serp_signals = select_best_candidate(
            serp_profiles, founder, len(serp_logins)
        )
        if serp_best is not None and serp_score > score:
            best, score, signals = serp_best, serp_score, serp_signals
            method = "serpapi"

    evidence: dict[str, Any] = {
        "matched_signals": signals,
        "candidate_login": best.get("login") if best else None,
    }
    if score < MIN_CONFIDENCE or best is None:
        evidence["reason"] = "best_candidate_below_threshold"
        return {
            "_founder_key": founder["_founder_key"],
            "gh_login": None,
            "gh_confidence": score,
            "resolution_method": "none",
                "evidence": json.dumps(evidence, sort_keys=True, separators=(",", ":")),
        }
    return {
        "_founder_key": founder["_founder_key"],
        "gh_login": best["login"],
        "gh_confidence": score,
        "resolution_method": method,
        "evidence": json.dumps(evidence, sort_keys=True, separators=(",", ":")),
    }


def save_resolution_checkpoint(
    rows: list[dict[str, Any]], state: dict[str, Any], output_path: Path
) -> None:
    frame = frame_from_rows(rows, RESOLUTION_SCHEMA).unique(
        subset=["_founder_key"], keep="last", maintain_order=True
    )
    atomic_write_parquet(frame, output_path)
    state["processed_founders"] = frame.height
    state["processed_keys"] = frame.get_column("_founder_key").to_list()
    atomic_write_json(state, checkpoint_path(output_path))


def resolve_founders(
    *,
    founders_path: Path = FOUNDERS_RAW_PATH,
    output_path: Path = FOUNDERS_RESOLVED_PATH,
    resolve_one: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> pl.DataFrame:
    """Resolve founders in descending batch order and resume every 50 rows."""
    if not founders_path.exists():
        raise FileNotFoundError(
            f"Missing {founders_path}; run the founders stage first"
        )
    founders = pl.read_parquet(founders_path).sort(
        "batch_start_date", descending=True, nulls_last=True
    )
    state_path = checkpoint_path(output_path)
    state = read_checkpoint(state_path)
    state.setdefault("serpapi_calls", 0)
    if output_path.exists():
        rows = pl.read_parquet(output_path).select(list(RESOLUTION_SCHEMA)).to_dicts()
    else:
        rows = []
    processed_keys = set(state.get("processed_keys", []))
    processed_keys.update(row["_founder_key"] for row in rows)
    pending = [
        row
        for row in founders.to_dicts()
        if row["_founder_key"] not in processed_keys
    ]
    started_at = time.monotonic()

    def process(resolver: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        for index, founder in enumerate(pending, start=1):
            rows.append(resolver(founder))
            if index % PROGRESS_INTERVAL == 0:
                elapsed = max(time.monotonic() - started_at, 0.001)
                resolved_count = sum(row["gh_login"] is not None for row in rows)
                LOGGER.info(
                    "Resolution progress founders=%d total=%d resolved=%d "
                    "rate=%.2f_founders_per_second",
                    index,
                    len(rows),
                    resolved_count,
                    index / elapsed,
                )
            if index % CHECKPOINT_INTERVAL == 0:
                save_resolution_checkpoint(rows, state, output_path)
                LOGGER.info(
                    "Resolution checkpoint founders=%d serpapi_calls=%d path=%s",
                    len(rows),
                    state["serpapi_calls"],
                    output_path,
                )

    try:
        if resolve_one is not None:
            process(resolve_one)
        else:
            tokens = read_github_tokens()
            cap_text = os.environ.get("SERPAPI_CAP", "300")
            try:
                cap = int(cap_text)
            except ValueError as error:
                raise InvalidSerpAPIConfigurationError(
                    "SERPAPI_CAP must be an integer"
                ) from error
            if cap < 0:
                raise InvalidSerpAPIConfigurationError(
                    "SERPAPI_CAP must be non-negative"
                )
            with GitHubClient(tokens) as github:
                def resolver(founder: dict[str, Any]) -> dict[str, Any]:
                    return resolve_founder(
                        founder,
                        github,
                        serpapi_key=os.environ.get("SERPAPI_API_KEY"),
                        serpapi_cap=cap,
                        state=state,
                        state_path=state_path,
                    )

                process(resolver)
    except BaseException:
        save_resolution_checkpoint(rows, state, output_path)
        raise

    save_resolution_checkpoint(rows, state, output_path)
    frame = pl.read_parquet(output_path)
    LOGGER.info("Resolution complete founders=%d path=%s", frame.height, output_path)
    return frame
