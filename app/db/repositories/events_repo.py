from __future__ import annotations

import aiosqlite

from app.db.connection import Database


class EventsRepo:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def record(
        self,
        attempt_id: int,
        user_id: int,
        question_id: int,
        selected_option: str | None,
        is_correct: bool,
        time_taken_ms: int | None = None,
    ) -> None:
        await self.db.conn.execute(
            """
            INSERT INTO events (
                attempt_id, user_id, question_id,
                selected_option, is_correct, time_taken_ms
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                attempt_id,
                user_id,
                question_id,
                selected_option,
                1 if is_correct else 0,
                time_taken_ms,
            ),
        )
        await self.db.conn.commit()

    async def stats_by_topic_for_user(self, user_id: int) -> list[aiosqlite.Row]:
        async with self.db.conn.execute(
            """
            SELECT q.topic AS topic,
                   COUNT(*) AS total,
                   SUM(e.is_correct) AS correct
            FROM events e
            JOIN questions q ON q.id = e.question_id
            WHERE e.user_id = ?
            GROUP BY q.topic
            ORDER BY q.topic
            """,
            (user_id,),
        ) as cur:
            return list(await cur.fetchall())

    async def total_for_user(self, user_id: int) -> tuple[int, int]:
        async with self.db.conn.execute(
            """
            SELECT COUNT(*) AS total, COALESCE(SUM(is_correct), 0) AS correct
            FROM events
            WHERE user_id = ?
            """,
            (user_id,),
        ) as cur:
            row = await cur.fetchone()
        if not row:
            return 0, 0
        return int(row[0]), int(row[1])
