from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class Job(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    company: str
    location: str
    description: str
    posted_at: datetime
    url: str
    source: str
    experience_years_min: int | None = None
    experience_years_max: int | None = None
    remote: bool = False
    raw: dict = Field(default_factory=dict)

    def __repr__(self) -> str:
        exp = (
            f"{self.experience_years_min}-{self.experience_years_max}yrs"
            if self.experience_years_min is not None or self.experience_years_max is not None
            else "exp=unspecified"
        )
        remote_tag = "remote" if self.remote else "onsite"
        return f"Job(title={self.title!r}, company={self.company!r}, {remote_tag}, {exp})"
