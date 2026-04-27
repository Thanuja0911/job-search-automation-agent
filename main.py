import argparse
import asyncio
import logging

import config
from adapters.orchestrator import run_all_adapters
from filters.dedup import Deduplicator
from filters.hard_filter import HardFilter
from scoring.engine import ScoringEngine
from storage.db import init_db


def main() -> None:
    parser = argparse.ArgumentParser(description="Job search automation agent")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would happen without writing to the database",
    )
    args = parser.parse_args()

    if args.dry_run:
        print(f"[dry-run] Would initialize database at {config.DB_PATH}")
        return

    init_db(config.DB_PATH)
    print(f"Database initialized at {config.DB_PATH}")

    jobs = asyncio.run(run_all_adapters())
    total = len(jobs)

    hard_filter = HardFilter()
    deduplicator = Deduplicator(config.DB_PATH)
    passed_jobs = []

    for job in jobs:
        passed, reason = hard_filter.evaluate(job)
        if not passed:
            logging.debug("Rejected [%s]: %s", reason, job)
            continue
        if deduplicator.is_duplicate(job):
            logging.debug("Rejected [duplicate]: %s", job)
            continue
        passed_jobs.append(job)

    print(
        f"Fetched: {total} | Passed filter: {len(passed_jobs)} | "
        f"Rejected: {total - len(passed_jobs)}"
    )

    if not passed_jobs:
        return

    engine = ScoringEngine()
    scored = sorted(
        [(job, engine.score(job)) for job in passed_jobs],
        key=lambda x: x[1].total_score,
        reverse=True,
    )

    print(f"\n{'#':<4} {'Score':<7} {'Title':<35} {'Company':<25} Matched Skills")
    print("-" * 100)
    for rank, (job, result) in enumerate(scored[:10], start=1):
        skills = ", ".join(result.matched_skills[:5])
        print(
            f"{rank:<4} {result.total_score:<7} "
            f"{job.title[:34]:<35} {job.company[:24]:<25} {skills}"
        )

    top = scored[0][1]
    avg = sum(r.total_score for _, r in scored) / len(scored)
    print(f"\nTop score: {top.total_score} | Avg score: {avg:.1f}")


if __name__ == "__main__":
    main()
