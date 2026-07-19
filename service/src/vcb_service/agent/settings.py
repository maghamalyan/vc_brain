"""Environment-backed deep-dive runtime settings."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Self


def workspace_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _integer(name: str, default: int, *, minimum: int = 1) -> int:
    raw = os.getenv(name)
    value = default if raw is None else int(raw)
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return value


@dataclass(frozen=True)
class AgentSettings:
    index_path: Path
    run_dir: Path
    cache_dir: Path
    openrouter_key: str | None
    openrouter_model: str
    serpapi_key: str | None
    max_concurrent: int
    daily_limit: int
    max_tool_calls: int
    max_gh_requests: int
    max_sql_chars: int
    max_output_chars: int
    model_request_limit: int

    @classmethod
    def from_env(cls, *, index_path: Path | None = None) -> Self:
        root = workspace_root()
        return cls(
            index_path=(index_path or Path(os.getenv("VCB_INDEX", root / "data/index/vcb.sqlite"))).resolve(),
            run_dir=Path(os.getenv("VCB_DEEPDIVE_DIR", root / "data/deepdives")).resolve(),
            cache_dir=Path(os.getenv("VCB_DEEPDIVE_CACHE", root / "data/cache/deepdive")).resolve(),
            openrouter_key=os.getenv("OPENROUTER_KEY"),
            openrouter_model=os.getenv(
                "OPENROUTER_MODEL", "anthropic/claude-sonnet-4.5"
            ),
            serpapi_key=os.getenv("SERPAPI_KEY"),
            max_concurrent=_integer("VCB_DEEPDIVE_MAX_CONCURRENT", 2),
            daily_limit=_integer("VCB_DEEPDIVE_DAILY_LIMIT", 30),
            max_tool_calls=_integer("VCB_AGENT_MAX_TOOL_CALLS", 100),
            max_gh_requests=_integer("VCB_AGENT_MAX_GH_REQUESTS", 12),
            max_sql_chars=_integer("VCB_AGENT_MAX_SQL_CHARS", 4_000),
            max_output_chars=_integer("VCB_AGENT_MAX_OUTPUT_CHARS", 20_000),
            model_request_limit=_integer("VCB_AGENT_MODEL_REQUEST_LIMIT", 30),
        )
