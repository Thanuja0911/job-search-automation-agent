from pydantic import BaseModel, Field


class ScoreResult(BaseModel):
    job_id: str
    total_score: float
    skill_score: float
    role_score: float
    exp_score: float
    stack_score: float
    domain_score: float
    matched_skills: list[str] = Field(default_factory=list)
    breakdown: dict = Field(default_factory=dict)
