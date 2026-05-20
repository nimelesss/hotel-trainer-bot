from __future__ import annotations

import json
import logging
from pathlib import Path

from app.db.connection import Database

log = logging.getLogger(__name__)

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


async def init_database(db: Database, seed_path: Path) -> None:
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    await db.conn.executescript(schema_sql)
    await db.conn.commit()
    log.info("Schema applied")

    await _seed_questions_if_empty(db, seed_path)


async def _seed_questions_if_empty(db: Database, seed_path: Path) -> None:
    async with db.conn.execute("SELECT COUNT(*) FROM questions") as cur:
        row = await cur.fetchone()
    count = row[0] if row else 0
    if count > 0:
        log.info("Questions table already has %d rows, skipping seed", count)
        return

    if not seed_path.exists():
        log.warning("Seed file %s does not exist, skipping seed", seed_path)
        return

    try:
        payload = json.loads(seed_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        log.error("Seed file %s is not valid JSON: %s", seed_path, e)
        return

    if not isinstance(payload, list):
        log.error("Seed file must contain a JSON array of question objects")
        return

    inserted = 0
    for item in payload:
        try:
            await db.conn.execute(
                """
                INSERT INTO questions (
                    topic, text,
                    option_a, option_b, option_c, option_d,
                    correct_option, explanation, law_reference,
                    difficulty, is_active, is_demo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item["topic"],
                    item["text"],
                    item["option_a"],
                    item["option_b"],
                    item["option_c"],
                    item["option_d"],
                    item["correct_option"],
                    item.get("explanation"),
                    item.get("law_reference"),
                    int(item.get("difficulty", 1)),
                    int(item.get("is_active", 1)),
                    int(item.get("is_demo", 0)),
                ),
            )
            inserted += 1
        except KeyError as e:
            log.warning("Seed item missing required field %s, skipped", e)
        except Exception as e:
            log.warning("Failed to insert seed item: %s", e)
    await db.conn.commit()
    log.info("Seeded %d question(s) from %s", inserted, seed_path)
