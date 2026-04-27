from datetime import datetime

from models.job import Job
from datetime import datetime, timedelta, timezone
UTC = timezone.utc

_US_EXPLICIT_TERMS = ("united states", "usa", ", us", "u.s.")

_US_STATE_NAMES = (
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana",
    "maine", "maryland", "massachusetts", "michigan", "minnesota",
    "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "new york",
    "north carolina", "north dakota", "ohio", "oklahoma", "oregon",
    "pennsylvania", "rhode island", "south carolina", "south dakota",
    "tennessee", "texas", "utah", "vermont", "virginia", "washington",
    "west virginia", "wisconsin", "wyoming", "district of columbia",
)

_CLEARANCE_TERMS = (
    "clearance required",
    "security clearance",
    "ts/sci",
    "top secret",
    "secret clearance",
    "public trust",
    "active clearance",
    "dod clearance",
    "clearance eligible",
)

_ROLE_TERMS = (
    "software",
    "engineer",
    "developer",
    "frontend",
    "backend",
    "full stack",
    "fullstack",
    "devops",
    "ml",
    "machine learning",
    "ai ",
    "applied ai",
    "full-stack",
    "new grad",
    "2026",
    "generative ai",
)


class HardFilter:
    def evaluate(self, job: Job) -> tuple[bool, str]:
        # 1. RECENCY
        age = datetime.now(UTC) - job.posted_at.replace(tzinfo=UTC)
        if age.total_seconds() > 86400:
            return (False, "posted over 24h ago")

        # 2. LOCATION
        if not job.remote:
            location_lower = job.location.lower()
            us_explicit = any(term in location_lower for term in _US_EXPLICIT_TERMS)
            us_state = any(state in location_lower for state in _US_STATE_NAMES)
            if not us_explicit and not us_state:
                return (False, "not US or remote")

        # 3. CLEARANCE
        combined = (job.description + " " + job.title).lower()
        if any(term in combined for term in _CLEARANCE_TERMS):
            return (False, "clearance required")

        # 4. EXPERIENCE
        if job.experience_years_min is not None and job.experience_years_min > 3:
            return (False, "experience too high")
        if job.experience_years_max is not None and job.experience_years_max > 5:
            return (False, "experience too high")

        # 5. ROLE TITLE
        title_lower = job.title.lower()
        if not any(term in title_lower for term in _ROLE_TERMS):
            return (False, "role not targeted")

        return (True, "passed")
