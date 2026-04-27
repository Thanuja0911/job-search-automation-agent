import hashlib
from datetime import datetime, timezone

from models.job import Job
from storage.db import get_db


class Deduplicator:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    def _hash(self, job: Job) -> str:
        key = f"{job.company.lower()}:{job.title.lower()}:{job.location.lower()}"
        return hashlib.sha256(key.encode()).hexdigest()

    def is_duplicate(self, job: Job) -> bool:
        h = self._hash(job)
        with get_db(self._db_path) as conn:
            row = conn.execute(
                "SELECT 1 FROM seen_hashes WHERE hash = ? LIMIT 1", (h,)
            ).fetchone()
        return row is not None

    def mark_seen(self, job: Job) -> None:
        h = self._hash(job)
        created_at = datetime.now(timezone.utc).isoformat()
        with get_db(self._db_path) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO seen_hashes (hash, job_id, created_at) VALUES (?, ?, ?)",
                (h, job.id, created_at),
            )
