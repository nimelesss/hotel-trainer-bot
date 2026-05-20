from __future__ import annotations

import aiosqlite

from app.db.connection import Database


class ReportsRepo:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def create(
        self,
        user_id: int,
        question_id: int,
        comment: str | None = None,
    ) -> int:
        cursor = await self.db.conn.execute(
            """
            INSERT INTO error_reports (user_id, question_id, comment)
            VALUES (?, ?, ?)
            """,
            (user_id, question_id, comment),
        )
        await self.db.conn.commit()
        return cursor.lastrowid or 0

    async def list_open(self, limit: int = 20) -> list[aiosqlite.Row]:
        async with self.db.conn.execute(
            """
            SELECT r.id, r.user_id, r.question_id, r.comment, r.created_at,
                   q.topic, q.text
            FROM error_reports r
            JOIN questions q ON q.id = r.question_id
            WHERE r.status = 'open'
            ORDER BY r.created_at ASC
            LIMIT ?
            """,
            (limit,),
        ) as cur:
            return list(await cur.fetchall())

    async def update_status(
        self,
        report_id: int,
        status: str,
        admin_note: str | None = None,
    ) -> None:
        await self.db.conn.execute(
            """
            UPDATE error_reports
            SET status = ?, admin_note = ?, reviewed_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, admin_note, report_id),
        )
        await self.db.conn.commit()

    async def count_open(self) -> int:
        async with self.db.conn.execute(
            "SELECT COUNT(*) FROM error_reports WHERE status = 'open'"
        ) as cur:
            row = await cur.fetchone()
        return row[0] if row else 0
