from models.job import Job
from models.score_result import ScoreResult
from scoring.dimensions import (
    score_domain_bonus,
    score_experience,
    score_role_match,
    score_skill_match,
    score_stack_overlap,
)


class ScoringEngine:
    def score(self, job: Job) -> ScoreResult:
        skill_score, matched_skills = score_skill_match(job)
        role_score = score_role_match(job)
        exp_score = score_experience(job)
        stack_score = score_stack_overlap(job)
        domain_score = score_domain_bonus(job)

        total = round(
            skill_score + role_score + exp_score + stack_score + domain_score, 1
        )

        return ScoreResult(
            job_id=job.id,
            total_score=total,
            skill_score=skill_score,
            role_score=role_score,
            exp_score=exp_score,
            stack_score=stack_score,
            domain_score=domain_score,
            matched_skills=matched_skills,
            breakdown={
                "skill": skill_score,
                "role": role_score,
                "experience": exp_score,
                "stack": stack_score,
                "domain": domain_score,
            },
        )
