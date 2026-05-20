-- Схема базы данных бота-тренажёра. Применяется один раз при создании bot.db.
-- Все CREATE используют IF NOT EXISTS, чтобы можно было перезапускать init безопасно.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    user_id        INTEGER PRIMARY KEY,
    username       TEXT,
    first_name     TEXT,
    last_name      TEXT,
    language_code  TEXT,
    is_blocked     INTEGER NOT NULL DEFAULT 0 CHECK (is_blocked IN (0, 1)),
    created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS questions (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    topic          TEXT NOT NULL,
    text           TEXT NOT NULL,
    option_a       TEXT NOT NULL,
    option_b       TEXT NOT NULL,
    option_c       TEXT NOT NULL,
    option_d       TEXT NOT NULL,
    correct_option TEXT NOT NULL CHECK (correct_option IN ('A', 'B', 'C', 'D')),
    explanation    TEXT,
    law_reference  TEXT,
    difficulty     INTEGER NOT NULL DEFAULT 1 CHECK (difficulty BETWEEN 1 AND 3),
    is_active      INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    is_demo        INTEGER NOT NULL DEFAULT 0 CHECK (is_demo IN (0, 1)),
    created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS attempts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    mode            TEXT NOT NULL CHECK (mode IN ('quick', 'exam', 'mistakes')),
    total_questions INTEGER NOT NULL CHECK (total_questions > 0),
    correct_count   INTEGER NOT NULL DEFAULT 0 CHECK (correct_count >= 0),
    status          TEXT NOT NULL DEFAULT 'in_progress'
                    CHECK (status IN ('in_progress', 'completed', 'abandoned')),
    started_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at     TIMESTAMP
);

CREATE TABLE IF NOT EXISTS events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id      INTEGER NOT NULL REFERENCES attempts(id) ON DELETE CASCADE,
    user_id         INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    question_id     INTEGER NOT NULL REFERENCES questions(id) ON DELETE RESTRICT,
    selected_option TEXT CHECK (selected_option IS NULL OR selected_option IN ('A', 'B', 'C', 'D')),
    is_correct      INTEGER NOT NULL CHECK (is_correct IN (0, 1)),
    time_taken_ms   INTEGER,
    answered_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS error_reports (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    question_id  INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    comment      TEXT,
    status       TEXT NOT NULL DEFAULT 'open'
                 CHECK (status IN ('open', 'reviewed', 'fixed', 'rejected')),
    admin_note   TEXT,
    created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_at  TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_events_user_correct   ON events(user_id, is_correct);
CREATE INDEX IF NOT EXISTS idx_events_attempt        ON events(attempt_id);
CREATE INDEX IF NOT EXISTS idx_events_question       ON events(question_id);
CREATE INDEX IF NOT EXISTS idx_questions_topic_act   ON questions(topic, is_active);
CREATE INDEX IF NOT EXISTS idx_attempts_user_status  ON attempts(user_id, status);
CREATE INDEX IF NOT EXISTS idx_reports_status        ON error_reports(status, created_at);
