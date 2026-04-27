from datetime import datetime, timedelta, timezone

from filters.dedup import Deduplicator
from filters.hard_filter import HardFilter
from models.job import Job
from storage.db import get_db, init_db

UTC = timezone.utc


def make_job(**kw):
    defaults = dict(
        title="Software Engineer",
        company="Acme",
        location="Remote, USA",
        description="Great role",
        posted_at=datetime.now(UTC),
        url="http://x.com",
        source="test",
    )
    defaults.update(kw)
    return Job(**defaults)


def test_passes_valid_job():
    passed, reason = HardFilter().evaluate(make_job())
    assert passed is True
    assert reason == "passed"


def test_rejects_old_job():
    job = make_job(posted_at=datetime.now(UTC) - timedelta(days=2))
    passed, reason = HardFilter().evaluate(job)
    assert passed is False
    assert reason == "posted over 24h ago"


def test_rejects_non_us_location():
    job = make_job(location="London, UK", remote=False)
    passed, reason = HardFilter().evaluate(job)
    assert passed is False
    assert reason == "not US or remote"


def test_accepts_remote_true():
    # remote=True should pass regardless of location string
    job = make_job(location="London, UK", remote=True)
    passed, reason = HardFilter().evaluate(job)
    assert passed is True
    assert reason == "passed"


def test_rejects_clearance_in_description():
    job = make_job(description="Active clearance required for this position")
    passed, reason = HardFilter().evaluate(job)
    assert passed is False
    assert reason == "clearance required"


def test_rejects_clearance_in_title():
    job = make_job(title="Software Engineer with TS/SCI")
    passed, reason = HardFilter().evaluate(job)
    assert passed is False
    assert reason == "clearance required"


def test_rejects_high_experience():
    job = make_job(experience_years_min=5)
    passed, reason = HardFilter().evaluate(job)
    assert passed is False
    assert reason == "experience too high"


def test_rejects_wrong_role():
    job = make_job(title="Marketing Manager")
    passed, reason = HardFilter().evaluate(job)
    assert passed is False
    assert reason == "role not targeted"


def test_accepts_us_state_in_location():
    job = make_job(location="San Francisco, California", remote=False)
    passed, reason = HardFilter().evaluate(job)
    assert passed is True
    assert reason == "passed"


# ---------------------------------------------------------------------------
# Deduplicator tests
# ---------------------------------------------------------------------------

def _store_job(db_path: str, job: Job) -> None:
    with get_db(db_path) as conn:
        conn.execute(
            "INSERT INTO jobs (id, title, company, location, description, "
            "posted_at, url, source, remote, fetched_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                job.id, job.title, job.company, job.location, job.description,
                job.posted_at.isoformat(), job.url, job.source,
                int(job.remote), job.posted_at.isoformat(),
            ),
        )


def test_new_job_is_not_duplicate(tmp_path):
    db = str(tmp_path / "test.db")
    init_db(db)
    job = make_job()
    d = Deduplicator(db)
    assert d.is_duplicate(job) is False


def test_same_job_twice_is_duplicate(tmp_path):
    db = str(tmp_path / "test.db")
    init_db(db)
    job = make_job()
    _store_job(db, job)
    d = Deduplicator(db)
    assert d.is_duplicate(job) is False
    d.mark_seen(job)
    assert d.is_duplicate(job) is True


def test_different_company_is_not_duplicate(tmp_path):
    db = str(tmp_path / "test.db")
    init_db(db)
    job_a = make_job(company="Acme")
    job_b = make_job(company="Beta")
    _store_job(db, job_a)
    d = Deduplicator(db)
    d.mark_seen(job_a)
    assert d.is_duplicate(job_b) is False
