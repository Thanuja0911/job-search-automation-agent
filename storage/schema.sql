CREATE TABLE IF NOT EXISTS runs (
    id               INTEGER PRIMARY KEY,
    started_at       TEXT    NOT NULL,
    finished_at      TEXT,
    jobs_fetched     INTEGER NOT NULL DEFAULT 0,
    jobs_passed_filter INTEGER NOT NULL DEFAULT 0,
    jobs_scored      INTEGER NOT NULL DEFAULT 0,
    jobs_stored      INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS jobs (
    id                   TEXT    PRIMARY KEY,
    title                TEXT    NOT NULL,
    company              TEXT    NOT NULL,
    location             TEXT    NOT NULL,
    description          TEXT    NOT NULL,
    posted_at            TEXT    NOT NULL,
    url                  TEXT    NOT NULL,
    source               TEXT    NOT NULL,
    experience_years_min INTEGER,
    experience_years_max INTEGER,
    remote               INTEGER NOT NULL DEFAULT 0,
    score                REAL,
    status               TEXT    NOT NULL DEFAULT 'new',
    fetched_at           TEXT    NOT NULL,
    run_id               INTEGER REFERENCES runs(id)
);

CREATE TABLE IF NOT EXISTS seen_hashes (
    hash       TEXT PRIMARY KEY,
    job_id     TEXT NOT NULL REFERENCES jobs(id),
    created_at TEXT NOT NULL
);
