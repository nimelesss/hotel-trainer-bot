from __future__ import annotations

import aiosqlite

from app.db.connection import Database


class AttemptsRepo:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def create(self, user_id: int, mode: str, total_questions: int) -> int:
        cursor = await self.db.conn.execute(
            """
            INSERT INTO attempts (user_id, mode, total_questions, status)
            VALUES (?, ?, ?, 'in_progress')
            """,
            (user_id, mode, total_questions),
        )
        await self.db.conn.commit()
        return cursor.lastrowid or 0

    async def increment_correct(self, attempt_id: int) -> None:
        await self.db.conn.execute(
            "UPDATE attempts SET correct_count = correct_count + 1 WHERE id = ?",
            (attempt_id,),
        )
        await self.db.conn.commit()

    async def finish(self, attempt_id: int) -> None:
        await self.db.conn.execute(
            """
            UPDATE attempts
            SET status = 'completed', finished_at = CURRENT_TIMESTAMP
            WHERE id = ? AND status = 'in_progress'
            """,
            (attempt_id,),
        )
        await self.db.conn.commit()

    async def abandon_active_for_user(self, user_id: int) -> None:
        await self.db.conn.execute(
            """
            UPDATE attempts
            SET status = 'abandoned', finished_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND status = 'in_progress'
            """,
            (user_id,),
        )
        await self.db.conn.commit()

    async def get(self, attempt_id: int) -> aiosqlite.Row | None:
        async with self.db.conn.execute(
            "SELECT * FROM attempts WHERE id = ?", (attempt_id,)
        ) as cur:
            return await cur.fetchone()

    async def count_completed_today(self) -> int:
        async with self.db.conn.execute(
            """
            SELECT COUNT(*) FROM attempts
            WHERE status = 'completed'
              AND DATE(finished_at) = DATE('now')
            """
        ) as cur:
            row = await cur.fetchone()
        return row[0] if row else 0
