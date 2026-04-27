from datetime import datetime, timezone

from models.job import Job
from scoring.engine import ScoringEngine

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


high_match_job = make_job(
    title="Full Stack Engineer",
    description=(
        "We use React, TypeScript, Node.js, AWS, Docker, LangChain, "
        "Python, FastAPI. AI-first startup, remote-friendly."
    ),
    experience_years_min=0,
    experience_years_max=2,
)

low_match_job = make_job(
    title="Data Entry Specialist",
    description="Microsoft Excel and data entry experience required.",
    experience_years_min=0,
    experience_years_max=1,
)


def test_high_match_scores_above_70():
    assert ScoringEngine().score(high_match_job).total_score >= 70


def test_low_match_scores_below_40():
    assert ScoringEngine().score(low_match_job).total_score < 40


def test_skill_score_bounded():
    result = ScoringEngine().score(high_match_job)
    assert 0 <= result.skill_score <= 35


def test_role_match_exact_target():
    job = make_job(title="Frontend Engineer")
    assert ScoringEngine().score(job).role_score == 25.0


def test_role_match_adjacent():
    job = make_job(title="Site Reliability Engineer")
    assert ScoringEngine().score(job).role_score == 10.0


def test_role_match_no_match():
    job = make_job(title="Accountant")
    assert ScoringEngine().score(job).role_score == 0.0


def test_matched_skills_populated():
    result = ScoringEngine().score(high_match_job)
    assert "react" in result.matched_skills


def test_breakdown_keys_present():
    result = ScoringEngine().score(high_match_job)
    assert set(result.breakdown.keys()) == {"skill", "role", "experience", "stack", "domain"}
