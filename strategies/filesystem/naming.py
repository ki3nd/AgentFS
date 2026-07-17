from __future__ import annotations

import re


def normalize_mount_path(slug: str) -> str:
    core = (slug or "").strip().strip("/").strip()
    # replace whitespace runs with a single dash; keep alnum, dash, underscore, slash
    core = re.sub(r"\s+", "-", core)
    core = re.sub(r"[^A-Za-z0-9_\-/]+", "-", core).strip("-/")
    if not core:
        raise ValueError(f"invalid mount slug: {slug!r}")
    return f"/{core}"
