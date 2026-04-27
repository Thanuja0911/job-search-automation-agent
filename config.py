import os

from dotenv import load_dotenv

load_dotenv()

_REQUIRED = ("ADZUNA_APP_ID", "ADZUNA_API_KEY", "JSEARCH_API_KEY")

_missing = [key for key in _REQUIRED if not os.environ.get(key)]
if _missing:
    raise RuntimeError(
        f"Missing required environment variable(s): {', '.join(_missing)}. "
        "Check your .env file or environment."
    )

ADZUNA_APP_ID: str = os.environ["ADZUNA_APP_ID"]
ADZUNA_API_KEY: str = os.environ["ADZUNA_API_KEY"]
JSEARCH_API_KEY: str = os.environ["JSEARCH_API_KEY"]
DB_PATH: str = os.environ.get("DB_PATH", "./jobs.db")
LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
