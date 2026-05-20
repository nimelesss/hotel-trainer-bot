from __future__ import annotations

from typing import Iterable

import aiosqlite

from app.db.connection import Database


class UsersRepo:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def upsert(
        self,
        user_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
        language_code: str | None,
    ) -> None:
        await self.db.conn.execute(
            """
            INSERT INTO users (user_id, username, first_name, last_name, language_code, last_seen_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_name = excluded.last_name,
                language_code = excluded.language_code,
                last_seen_at = CURRENT_TIMESTAMP,
                is_blocked = 0
            """,
            (user_id, username, first_name, last_name, language_code),
        )
        await self.db.conn.commit()

    async def mark_blocked(self, user_id: int, blocked: bool = True) -> None:
        await self.db.conn.execute(
            "UPDATE users SET is_blocked = ? WHERE user_id = ?",
            (1 if blocked else 0, user_id),
        )
        await self.db.conn.commit()

    async def all_active_ids(self) -> list[int]:
        async with self.db.conn.execute(
            "SELECT user_id FROM users WHERE is_blocked = 0"
        ) as cur:
            rows = await cur.fetchall()
        return [r[0] for r in rows]

    async def total_count(self) -> int:
        async with self.db.conn.execute("SELECT COUNT(*) FROM users") as cur:
            row = await cur.fetchone()
        return row[0] if row else 0

    async def get(self, user_id: int) -> aiosqlite.Row | None:
        async with self.db.conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cur:
            return await cur.fetchone()
