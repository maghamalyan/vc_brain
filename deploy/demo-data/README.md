# Frozen Railway demo snapshot

This directory is the only generated dataset admitted to the Railway image. It
contains public-derived, read-only inputs for 100 candidates. The production
image verifies every file against `manifest.json`, builds one SQLite read model,
and then discards these source files.

The snapshot deliberately excludes raw research data, caches, credentials,
live-agent runs, and local integration output. To replace it, rerun the verified
integration pipeline, copy only the same minimal file families, update the
manifest timestamp, counts, and SHA-256 values, and run the deployment test
suite before publishing.
