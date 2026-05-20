"""CLI для импорта боевой базы вопросов в SQLite.

Использование:
    python scripts/import_questions.py path/to/questions.json
    python scripts/import_questions.py path/to/questions.json --replace-demo
    python scripts/import_questions.py path/to/questions.json --deactivate-demo

Ожидаемый формат JSON: массив объектов с полями
    topic, text, option_a, option_b, option_c, option_d,
    correct_option ('A'|'B'|'C'|'D'),
    explanation (опц.), law_reference (опц.),
    difficulty (опц., 1–3), is_active (опц., 0|1).

is_demo выставляется в 0 для импортируемых вопросов автоматически.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# Делаем папку проекта доступной для импорта app.*
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.connection import Database  # noqa: E402
from config import Config, setup_logging  # noqa: E402

log = logging.getLogger("import_questions")


REQUIRED_FIELDS = (
    "topic", "text",
    "option_a", "option_b", "option_c", "option_d",
    "correct_option",
)


async def import_questions(
    db: Database,
    items: list[dict],
    replace_demo: bool,
    deactivate_demo: bool,
) -> tuple[int, int]:
    if replace_demo:
        await db.conn.execute("DELETE FROM questions WHERE is_demo = 1")
        await db.conn.commit()
        log.info("Demo questions deleted")
    elif deactivate_demo:
        await db.conn.execute("UPDATE questions SET is_active = 0 WHERE is_demo = 1")
        await db.conn.commit()
        log.info("Demo questions deactivated")

    inserted = 0
    skipped = 0
    for idx, item in enumerate(items, start=1):
        missing = [f for f in REQUIRED_FIELDS if f not in item]
        if missing:
            log.warning("Item #%d missing fields %s, skipped", idx, missing)
            skipped += 1
            continue
        if item["correct_option"] not in {"A", "B", "C", "D"}:
            log.warning(
                "Item #%d has invalid correct_option %r, skipped",
                idx, item["correct_option"],
            )
            skipped += 1
            continue
        try:
            await db.conn.execute(
                """
                INSERT INTO questions (
                    topic, text,
                    option_a, option_b, option_c, option_d,
                    correct_option, explanation, law_reference,
                    difficulty, is_active, is_demo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    item["topic"], item["text"],
                    item["option_a"], item["option_b"],
                    item["option_c"], item["option_d"],
                    item["correct_option"],
                    item.get("explanation"),
                    item.get("law_reference"),
                    int(item.get("difficulty", 1)),
                    int(item.get("is_active", 1)),
                ),
            )
            inserted += 1
        except Exception as e:
            log.warning("Item #%d failed: %s", idx, e)
            skipped += 1
    await db.conn.commit()
    return inserted, skipped


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Import questions from JSON into bot.db")
    p.add_argument("path", type=Path, help="Путь к JSON-файлу с вопросами")
    group = p.add_mutually_exclusive_group()
    group.add_argument(
        "--replace-demo", action="store_true",
        help="Удалить все вопросы с is_demo=1 перед импортом",
    )
    group.add_argument(
        "--deactivate-demo", action="store_true",
        help="Перевести демо-вопросы в is_active=0, не удаляя",
    )
    return p.parse_args()


async def main() -> int:
    args = parse_args()
    config = Config.load()
    setup_logging(config.log_level)

    if not args.path.exists():
        log.error("File not found: %s", args.path)
        return 2

    try:
        items = json.loads(args.path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        log.error("Invalid JSON: %s", e)
        return 2
    if not isinstance(items, list):
        log.error("Top-level JSON must be an array")
        return 2

    db = Database(config.db_path)
    await db.connect()
    try:
        inserted, skipped = await import_questions(
            db, items,
            replace_demo=args.replace_demo,
            deactivate_demo=args.deactivate_demo,
        )
    finally:
        await db.close()

    log.info("Done: %d inserted, %d skipped", inserted, skipped)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
