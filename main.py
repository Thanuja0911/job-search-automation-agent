import argparse

import config
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


if __name__ == "__main__":
    main()
