"""Identity-field normalization used by founder and GitHub matching."""

import re
import unicodedata
from urllib.parse import urlparse


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    ascii_value = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    )
    return " ".join(re.findall(r"[a-z0-9]+", ascii_value.lower()))


def normalize_domain(value: str | None) -> str | None:
    if not value:
        return None
    candidate = value.strip()
    try:
        parsed = urlparse(candidate if "://" in candidate else f"//{candidate}")
        host = parsed.hostname
    except ValueError:
        # Garbage like "[object Object]" parses as a bracketed IPv6 host and
        # raises deep inside urllib (observed live 2026-07-19).
        return None
    if not host:
        return None
    host = host.lower().rstrip(".")
    return host[4:] if host.startswith("www.") else host


def twitter_handle(value: str | None) -> str | None:
    if not value:
        return None
    candidate = value.strip().rstrip("/")
    if "://" in candidate or candidate.startswith("www."):
        parsed = urlparse(
            candidate if "://" in candidate else f"https://{candidate}"
        )
        candidate = parsed.path.strip("/").split("/")[0]
    candidate = candidate.lstrip("@").strip()
    return candidate.lower() or None


def founder_key(slug: str, founder_name: str, user_id: object = None) -> str:
    identity = str(user_id).strip() if user_id is not None else ""
    if not identity:
        identity = normalize_text(founder_name)
    return f"{slug}:{identity}"
