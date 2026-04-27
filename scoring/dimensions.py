from models.job import Job
from scoring.profile import (
    AI_KEYWORDS,
    ADJACENT_ROLES,
    CLOUD_KEYWORDS,
    DOMAIN_BONUS_KEYWORDS,
    SKILL_WEIGHTS,
    TARGET_ROLES,
)

# Computed once at import — sum of the 8 highest skill weights.
# Used as the ceiling for score_skill_match normalisation.
_TOP8_MAX = sum(sorted(SKILL_WEIGHTS.values(), reverse=True)[:8])


def score_skill_match(job: Job) -> tuple[float, list[str]]:
    text = (job.description + " " + job.title).lower()
    matched = [skill for skill in SKILL_WEIGHTS if skill in text]
    total = sum(SKILL_WEIGHTS[s] for s in matched)
    return min(35.0, (total / _TOP8_MAX) * 35.0), matched


def score_role_match(job: Job) -> float:
    title = job.title.lower()
    if any(role in title for role in TARGET_ROLES):
        return 25.0
    if any(role in title for role in ADJACENT_ROLES):
        return 10.0
    return 0.0


def score_experience(job: Job) -> float:
    exp_max = job.experience_years_max
    exp_min = job.experience_years_min
    if exp_max is None and exp_min is None:
        return 10.0
    val = exp_max if exp_max is not None else exp_min
    if val <= 1:
        return 20.0
    if val <= 2:
        return 16.0
    if val <= 3:
        return 12.0
    return 8.0


def score_stack_overlap(job: Job) -> float:
    text = (job.description + " " + job.title).lower()
    cloud_hits = sum(1 for kw in CLOUD_KEYWORDS if kw in text)
    ai_hits = sum(1 for kw in AI_KEYWORDS if kw in text)
    return min(8.0, cloud_hits * 2.0) + min(7.0, ai_hits * 2.5)


def score_domain_bonus(job: Job) -> float:
    text = (job.description + " " + job.title + " " + job.company).lower()
    total = sum(pts for kw, pts in DOMAIN_BONUS_KEYWORDS.items() if kw in text)
    return min(5.0, float(total))
