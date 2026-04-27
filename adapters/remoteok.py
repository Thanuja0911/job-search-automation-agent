import asyncio
import logging
from datetime import datetime

import httpx

from adapters.base import BaseAdapter
from models.job import Job

logger = logging.getLogger(__name__)

_BASE_URL = "https://remoteok.com/api"
_TIMEOUT = 10.0
_MAX_RETRIES = 3
_HEADERS = {"User-Agent": "job-search-agent/1.0"}
_RELEVANT_TAGS: frozenset[str] = frozenset({
    "software", "javascript", "python", "react", "node",
    "devops", "backend", "frontend", "fullstack", "ml", "ai", "langchain", "fastapi", "django"
})


class RemoteOKAdapter(BaseAdapter):
    async def fetch(self) -> list[Job]:
        response = None
        async with httpx.AsyncClient(timeout=_TIMEOUT, headers=_HEADERS) as client:
            for attempt in range(1, _MAX_RETRIES + 1):
                try:
                    response = await client.get(_BASE_URL)
                    response.raise_for_status()
                    break
                except httpx.RequestError as exc:
                    logger.warning(
                        "RemoteOK network error (attempt %d/%d): %s",
                        attempt,
                        _MAX_RETRIES,
                        exc,
                    )
                    if attempt < _MAX_RETRIES:
                        await asyncio.sleep(attempt)
                    else:
                        raise

        raw_list = response.json()[1:]  # index 0 is metadata

        jobs = []
        for raw in raw_list:
            tags = set(raw.get("tags") or [])
            if not tags & _RELEVANT_TAGS:
                continue
            job = self._normalize(raw)
            if job is not None:
                jobs.append(job)
        return jobs

    def _normalize(self, raw: dict) -> Job | None:
        try:
            date_val = raw.get("date")
            if not date_val:
                return None
            # posted_at = datetime.utcfromtimestamp(int(date_val))
            try:
                posted_at = datetime.utcfromtimestamp(int(date_val))
            except (ValueError, TypeError):
                posted_at = datetime.fromisoformat(date_val)

            return Job(
                title=raw.get("position", ""),
                company=raw.get("company", ""),
                location=raw.get("location") or "Remote, USA",
                description=raw.get("description", ""),
                posted_at=posted_at,
                url=raw.get("url", ""),
                source="remoteok",
                experience_years_min=None,
                experience_years_max=None,
                remote=True,
                raw=raw,
            )
        except Exception as exc:
            logger.warning("Failed to normalize RemoteOK result: %s", exc)
            return None
