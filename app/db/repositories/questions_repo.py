from __future__ import annotations

import aiosqlite

from app.db.connection import Database


class QuestionsRepo:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def get(self, question_id: int) -> aiosqlite.Row | None:
        async with self.db.conn.execute(
            "SELECT * FROM questions WHERE id = ?", (question_id,)
        ) as cur:
            return await cur.fetchone()

    async def pick_random_active(self, limit: int) -> list[aiosqlite.Row]:
        async with self.db.conn.execute(
            """
            SELECT * FROM questions
            WHERE is_active = 1
            ORDER BY RANDOM()
            LIMIT ?
            """,
            (limit,),
        ) as cur:
            return list(await cur.fetchall())

    async def pick_user_mistakes(self, user_id: int, limit: int) -> list[aiosqlite.Row]:
        # Берём вопросы, по которым ПОСЛЕДНИЙ ответ пользователя был неверным.
        # Если потом он ответил правильно — вопрос из списка ошибок уходит.
        async with self.db.conn.execute(
            """
            WITH last_per_question AS (
                SELECT question_id, is_correct,
                       ROW_NUMBER() OVER (PARTITION BY question_id ORDER BY answered_at DESC) AS rn
                FROM events
                WHERE user_id = ?
            )
            SELECT q.*
            FROM questions q
            JOIN last_per_question lpq ON lpq.question_id = q.id
            WHERE lpq.rn = 1
              AND lpq.is_correct = 0
              AND q.is_active = 1
            ORDER BY RANDOM()
            LIMIT ?
            """,
            (user_id, limit),
        ) as cur:
            return list(await cur.fetchall())

    async def total_active_count(self) -> int:
        async with self.db.conn.execute(
            "SELECT COUNT(*) FROM questions WHERE is_active = 1"
        ) as cur:
            row = await cur.fetchone()
        return row[0] if row else 0

    async def set_active(self, question_id: int, is_active: bool) -> None:
        await self.db.conn.execute(
            "UPDATE questions SET is_active = ? WHERE id = ?",
            (1 if is_active else 0, question_id),
        )
        await self.db.conn.commit()
