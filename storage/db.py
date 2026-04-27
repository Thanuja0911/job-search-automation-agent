import sqlite3
from contextlib import contextmanager
from pathlib import Path


def get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: str) -> None:
    schema = (Path(__file__).parent / "schema.sql").read_text()
    conn = get_connection(db_path)
    try:
        conn.executescript(schema)
    finally:
        conn.close()


@contextmanager
def get_db(db_path: str):
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
