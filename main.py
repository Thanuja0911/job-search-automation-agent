import argparse
import asyncio

import config
from adapters.orchestrator import run_all_adapters
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
    print(f"Fetched {len(jobs)} jobs from all sources")
    for job in jobs[:3]:
        print(job)


if __name__ == "__main__":
    main()
