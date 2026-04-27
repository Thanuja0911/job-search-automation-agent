import asyncio
import logging
from datetime import datetime

import httpx

import config
from adapters.base import BaseAdapter
from models.job import Job

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.adzuna.com/v1/api/jobs/us/search/1"
_RESULTS_PER_PAGE = 50
_TIMEOUT = 10.0
_MAX_RETRIES = 3
_SEARCH_TERMS = [
    "software engineer",
    "ai engineer",
    "full stack developer",
    "frontend developer",
    "backend developer",
    "devops engineer",
    "machine learning engineer",
]


class AdzunaAdapter(BaseAdapter):
    def __init__(self) -> None:
        self._app_id = config.ADZUNA_APP_ID
        self._app_key = config.ADZUNA_API_KEY

    async def fetch(self) -> list[Job]:
        jobs: list[Job] = []
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            for term in _SEARCH_TERMS:
                results = await self._fetch_term(client, term)
                jobs.extend(results)
        return jobs

    async def _fetch_term(self, client: httpx.AsyncClient, term: str) -> list[Job]:
        params = {
            "app_id": self._app_id,
            "app_key": self._app_key,
            "results_per_page": _RESULTS_PER_PAGE,
            "what": term,
            "where": "united states",
            "max_days_old": 1,
            "sort_by": "date",
        }

        response = None
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                response = await client.get(_BASE_URL, params=params)
                response.raise_for_status()
                break
            except httpx.RequestError as exc:
                logger.warning(
                    "Adzuna network error for %r (attempt %d/%d): %s",
                    term,
                    attempt,
                    _MAX_RETRIES,
                    exc,
                )
                if attempt < _MAX_RETRIES:
                    await asyncio.sleep(attempt)
                else:
                    raise

        raw_results = response.json().get("results", [])
        jobs = []
        for raw in raw_results:
            job = self._normalize(raw)
            if job is not None:
                jobs.append(job)
        return jobs

    def _normalize(self, raw: dict) -> Job | None:
        try:
            title = raw.get("title", "")
            location = raw.get("location", {}).get("display_name", "")
            remote = "remote" in title.lower() or "remote" in location.lower()

            created = raw.get("created")
            if not created:
                return None
            posted_at = datetime.fromisoformat(created)

            return Job(
                title=title,
                company=raw.get("company", {}).get("display_name", ""),
                location=location,
                description=raw.get("description", ""),
                posted_at=posted_at,
                url=raw.get("redirect_url", ""),
                source="adzuna",
                experience_years_min=None,
                experience_years_max=None,
                remote=remote,
                raw=raw,
            )
        except Exception as exc:
            logger.warning("Failed to normalize Adzuna result: %s", exc)
            return None
