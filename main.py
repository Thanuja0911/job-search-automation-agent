import argparse
import asyncio
import logging
from datetime import datetime
from pathlib import Path

import config
from adapters.orchestrator import run_all_adapters
from filters.dedup import Deduplicator
from filters.hard_filter import HardFilter
from output.reporter import generate_markdown_report, print_terminal_table
from scoring.engine import ScoringEngine
from storage.db import init_db
from storage.tracker import JobTracker


def main() -> None:
    parser = argparse.ArgumentParser(description="Job search automation agent")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch, filter, and score without writing to the database",
    )
    args = parser.parse_args()

    init_db(config.DB_PATH)
    print(f"Database initialized at {config.DB_PATH}")

    jobs_raw = asyncio.run(run_all_adapters())
    total = len(jobs_raw)

    hard_filter = HardFilter()
    deduplicator = Deduplicator(config.DB_PATH)
    passed_jobs = []

    for job in jobs_raw:
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

    stored_count = 0
    if not args.dry_run:
        tracker = JobTracker(config.DB_PATH)
        for job, result in scored:
            tracker.upsert_job(job, result)
            deduplicator.mark_seen(job)
            stored_count += 1
        top_jobs = tracker.get_top_jobs(limit=25, min_score=40.0)
    else:
        top_jobs = [
            {
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "posted_at": job.posted_at.isoformat(),
                "source": job.source,
                "url": job.url,
                "score": result.total_score,
            }
            for job, result in scored[:25]
            if result.total_score >= 40.0
        ]

    print_terminal_table(top_jobs)

    top_score = scored[0][1].total_score if scored else 0.0
    avg_score = sum(r.total_score for _, r in scored) / len(scored)
    run_stats = {
        "fetched": total,
        "passed": len(passed_jobs),
        "scored": len(scored),
        "stored": stored_count,
        "top_score": top_score,
    }
    print(f"\nTop score: {top_score} | Avg score: {avg_score:.1f}")

    report_md = generate_markdown_report(top_jobs, run_stats)

    if not args.dry_run:
        Path("output").mkdir(exist_ok=True)
        filename = datetime.now().strftime("%Y-%m-%d") + ".md"
        report_path = Path("output") / filename
        report_path.write_text(report_md)
        print(f"Report saved to output/{filename}")
    else:
        print("(dry run — nothing stored)")


if __name__ == "__main__":
    main()
