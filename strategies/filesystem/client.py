from __future__ import annotations

import logging
from typing import Any

import httpx

from strategies.filesystem.aio import run_coroutine_sync

logger = logging.getLogger(__name__)


class DatasetMetadataClient:
    def __init__(self, base_url: str, api_key: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._transport: httpx.BaseTransport | None = None  # test hook
        self._cache: dict[str, dict[str, str]] | None = None

    def get(self, dataset_id: str) -> dict[str, str]:
        try:
            all_meta = self._ensure_loaded()
        except Exception:  # noqa: BLE001
            logger.exception("Dataset metadata fetch failed")
            return {"name": dataset_id, "description": ""}
        return all_meta.get(dataset_id, {"name": dataset_id, "description": ""})

    def fetch_all(self) -> dict[str, dict[str, str]]:
        return self._ensure_loaded()

    def _ensure_loaded(self) -> dict[str, dict[str, str]]:
        if self._cache is None:
            self._cache = run_coroutine_sync(lambda: self._afetch_all())
        return self._cache

    async def _afetch_all(self) -> dict[str, dict[str, str]]:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        results: dict[str, dict[str, str]] = {}
        page = 1
        async with httpx.AsyncClient(
            timeout=30, transport=self._transport
        ) as client:
            while True:
                resp = await client.get(
                    f"{self._base_url}/datasets",
                    headers=headers,
                    params={"page": page, "limit": 100},
                )
                resp.raise_for_status()
                payload: dict[str, Any] = resp.json()
                for item in payload.get("data") or []:
                    ds_id = item.get("id")
                    if ds_id is None:
                        continue
                    results[str(ds_id)] = {
                        "name": item.get("name") or str(ds_id),
                        "description": item.get("description") or "",
                    }
                if not payload.get("has_more"):
                    return results
                page += 1
