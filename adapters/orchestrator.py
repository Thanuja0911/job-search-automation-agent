import asyncio
import logging

from adapters.adzuna import AdzunaAdapter
from adapters.remoteok import RemoteOKAdapter
from models.job import Job

logger = logging.getLogger(__name__)


async def run_all_adapters() -> list[Job]:
    adapters = [AdzunaAdapter(), RemoteOKAdapter()]
    results = await asyncio.gather(
        *[adapter.fetch() for adapter in adapters],
        return_exceptions=True,
    )

    jobs: list[Job] = []
    for adapter, result in zip(adapters, results):
        if isinstance(result, Exception):
            logger.error(
                "Adapter %s failed: %s",
                type(adapter).__name__,
                result,
            )
        else:
            jobs.extend(result)
    return jobs
