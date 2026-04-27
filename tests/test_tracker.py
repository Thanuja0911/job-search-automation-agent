from datetime import datetime, timezone
from pathlib import Path

import pytest

from models.job import Job
from models.score_result import ScoreResult
from storage.db import init_db
from storage.tracker import JobTracker


def make_job(**kwargs) -> Job:
    defaults = {
        "title": "Software Engineer",
        "company": "Acme Corp",
        "location": "Remote",
        "description": "Python, FastAPI, AWS",
        "posted_at": datetime.now(timezone.utc),
        "url": "https://example.com/job/1",
        "source": "adzuna",
        "experience_years_min": 1,
        "experience_years_max": 3,
        "remote": True,
        "raw": {},
    }
    defaults.update(kwargs)
    return Job(**defaults)


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "test.db")
    init_db(path)
    return path


@pytest.fixture
def job() -> Job:
    return make_job()


@pytest.fixture
def score_result(job: Job) -> ScoreResult:
    return ScoreResult(
        job_id=job.id,
        total_score=82.5,
        skill_score=30.0,
        role_score=25.0,
        exp_score=16.0,
        stack_score=7.0,
        domain_score=4.5,
        matched_skills=["python", "fastapi", "aws"],
        breakdown={
            "skill": 30.0,
            "role": 25.0,
            "experience": 16.0,
            "stack": 7.0,
            "domain": 4.5,
        },
    )


def test_upsert_stores_job(db_path: str, job: Job, score_result: ScoreResult) -> None:
    tracker = JobTracker(db_path)
    tracker.upsert_job(job, score_result)
    assert tracker.job_count() == 1


def test_upsert_is_idempotent(db_path: str, job: Job, score_result: ScoreResult) -> None:
    tracker = JobTracker(db_path)
    tracker.upsert_job(job, score_result)
    tracker.upsert_job(job, score_result)
    assert tracker.job_count() == 1


def test_get_top_jobs_returns_sorted(db_path: str) -> None:
    tracker = JobTracker(db_path)
    jobs_and_scores = [
        (make_job(title="Job A", url="https://example.com/a"), 45.0),
        (make_job(title="Job B", url="https://example.com/b"), 82.0),
        (make_job(title="Job C", url="https://example.com/c"), 61.0),
    ]
    for job, total in jobs_and_scores:
        result = ScoreResult(
            job_id=job.id,
            total_score=total,
            skill_score=0.0,
            role_score=0.0,
            exp_score=total,
            stack_score=0.0,
            domain_score=0.0,
            matched_skills=[],
            breakdown={},
        )
        tracker.upsert_job(job, result)

    top = tracker.get_top_jobs(limit=10, min_score=0.0)
    scores = [row["score"] for row in top]
    assert scores == [82.0, 61.0, 45.0]


def test_get_top_jobs_respects_min_score(db_path: str) -> None:
    tracker = JobTracker(db_path)
    for title, url, total in [
        ("High", "https://example.com/high", 85.0),
        ("Mid", "https://example.com/mid", 55.0),
        ("Low", "https://example.com/low", 30.0),
    ]:
        job = make_job(title=title, url=url)
        result = ScoreResult(
            job_id=job.id,
            total_score=total,
            skill_score=0.0,
            role_score=0.0,
            exp_score=total,
            stack_score=0.0,
            domain_score=0.0,
            matched_skills=[],
            breakdown={},
        )
        tracker.upsert_job(job, result)

    top = tracker.get_top_jobs(limit=10, min_score=60.0)
    assert len(top) == 1
    assert top[0]["score"] == 85.0


def test_update_status(db_path: str, job: Job, score_result: ScoreResult) -> None:
    tracker = JobTracker(db_path)
    tracker.upsert_job(job, score_result)
    tracker.update_status(job.id, "applied")
    top = tracker.get_top_jobs(limit=10, min_score=0.0)
    assert len(top) == 0
