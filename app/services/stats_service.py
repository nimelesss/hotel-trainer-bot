from __future__ import annotations

from dataclasses import dataclass

from app.db.repositories.attempts_repo import AttemptsRepo
from app.db.repositories.events_repo import EventsRepo
from app.db.repositories.questions_repo import QuestionsRepo
from app.db.repositories.reports_repo import ReportsRepo
from app.db.repositories.users_repo import UsersRepo


@dataclass
class UserStats:
    total: int
    correct: int
    per_topic: list[tuple[str, int, int]]  # (topic, correct, total)


@dataclass
class AdminStats:
    users_total: int
    questions_active: int
    attempts_today: int
    reports_open: int


class StatsService:
    def __init__(
        self,
        users_repo: UsersRepo,
        events_repo: EventsRepo,
        questions_repo: QuestionsRepo,
        attempts_repo: AttemptsRepo,
        reports_repo: ReportsRepo,
    ) -> None:
        self.users = users_repo
        self.events = events_repo
        self.questions = questions_repo
        self.attempts = attempts_repo
        self.reports = reports_repo

    async def user_stats(self, user_id: int) -> UserStats:
        total, correct = await self.events.total_for_user(user_id)
        per_topic_rows = await self.events.stats_by_topic_for_user(user_id)
        per_topic = [
            (row["topic"], int(row["correct"] or 0), int(row["total"]))
            for row in per_topic_rows
        ]
        return UserStats(total=total, correct=correct, per_topic=per_topic)

    async def admin_stats(self) -> AdminStats:
        return AdminStats(
            users_total=await self.users.total_count(),
            questions_active=await self.questions.total_active_count(),
            attempts_today=await self.attempts.count_completed_today(),
            reports_open=await self.reports.count_open(),
        )
