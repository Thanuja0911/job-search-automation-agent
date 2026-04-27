from datetime import datetime, timezone

from models.job import Job
from models.score_result import ScoreResult
from storage.db import get_db


class JobTracker:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    def upsert_job(
        self, job: Job, score: ScoreResult, run_id: int | None = None
    ) -> None:
        fetched_at = datetime.now(timezone.utc).isoformat()
        with get_db(self._db_path) as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO jobs (
                    id, title, company, location, description, posted_at,
                    url, source, experience_years_min, experience_years_max,
                    remote, score, status, fetched_at, run_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.id,
                    job.title,
                    job.company,
                    job.location,
                    job.description,
                    job.posted_at.isoformat(),
                    job.url,
                    job.source,
                    job.experience_years_min,
                    job.experience_years_max,
                    int(job.remote),
                    score.total_score,
                    "new",
                    fetched_at,
                    run_id,
                ),
            )

    def get_top_jobs(
        self, limit: int = 25, min_score: float = 40.0
    ) -> list[dict]:
        with get_db(self._db_path) as conn:
            rows = conn.execute(
                """
                SELECT * FROM jobs
                WHERE score >= ? AND status = 'new'
                ORDER BY score DESC
                LIMIT ?
                """,
                (min_score, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def update_status(self, job_id: str, status: str) -> None:
        with get_db(self._db_path) as conn:
            conn.execute(
                "UPDATE jobs SET status = ? WHERE id = ?",
                (status, job_id),
            )

    def job_count(self) -> int:
        with get_db(self._db_path) as conn:
            return conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
