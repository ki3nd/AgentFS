from __future__ import annotations

from pydantic import BaseModel, Field

from strategies.filesystem.naming import normalize_mount_path


def parse_mounts(raw: str | dict | None) -> dict[str, str]:
    pairs: list[tuple[str, str]] = []
    if raw is None:
        pass
    elif isinstance(raw, dict):
        pairs = [(str(k), str(v)) for k, v in raw.items()]
    else:
        for line in str(raw).splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if ":" not in stripped:
                raise ValueError(f"mount line missing ':' -> {line!r}")
            slug, _, ds_id = stripped.partition(":")
            pairs.append((slug, ds_id))

    mounts: dict[str, str] = {}
    for slug, ds_id in pairs:
        dataset_id = ds_id.strip()
        if not dataset_id:
            raise ValueError(f"mount for slug {slug!r} has empty dataset id")
        mount_path = normalize_mount_path(slug)
        if mount_path in mounts:
            raise ValueError(f"duplicate mount path: {mount_path}")
        mounts[mount_path] = dataset_id
    return mounts


class FilesystemConfig(BaseModel):
    mounts: dict[str, str] = Field(min_length=1)
    truncate_kb: int = Field(default=50, ge=1, le=1024)
    expose_semantic_search: bool = True
    include_workspace_tree: bool = True
    slug_metadata_name: str = "slug"
