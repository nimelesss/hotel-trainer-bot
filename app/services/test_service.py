from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import aiosqlite

from app.db.repositories.attempts_repo import AttemptsRepo
from app.db.repositories.questions_repo import QuestionsRepo
from app.utils.texts import EXAM_SIZE, MISTAKES_SIZE, QUICK_TEST_SIZE


MODE_SIZES = {
    "quick": QUICK_TEST_SIZE,
    "exam": EXAM_SIZE,
    "mistakes": MISTAKES_SIZE,
}


@dataclass
class StartedTest:
    attempt_id: int
    question_ids: list[int]
    mode: str


class TestService:
    def __init__(
        self,
        questions_repo: QuestionsRepo,
        attempts_repo: AttemptsRepo,
    ) -> None:
        self.questions = questions_repo
        self.attempts = attempts_repo

    async def pick_questions(
        self, user_id: int, mode: str, topic: str | None = None
    ) -> list[aiosqlite.Row]:
        if mode not in MODE_SIZES:
            raise ValueError(f"Unknown mode: {mode}")
        size = MODE_SIZES[mode]
        if mode == "mistakes":
            if topic is None:
                return await self.questions.pick_user_mistakes(user_id, size)
            return await self.questions.pick_user_mistakes_by_topic(
                user_id, topic, size
            )
        if topic is None:
            return await self.questions.pick_random_active(size)
        return await self.questions.pick_random_active_by_topic(topic, size)

    async def start(
        self, user_id: int, mode: str, questions: Sequence[aiosqlite.Row]
    ) -> StartedTest:
        question_ids = [q["id"] for q in questions]
        # Прежняя незавершённая попытка пользователя — в abandoned, чтобы не было двух in_progress.
        await self.attempts.abandon_active_for_user(user_id)
        attempt_id = await self.attempts.create(
            user_id=user_id, mode=mode, total_questions=len(question_ids)
        )
        return StartedTest(
            attempt_id=attempt_id, question_ids=question_ids, mode=mode
        )

    @staticmethod
    def is_correct(question: aiosqlite.Row, selected: str) -> bool:
        return question["correct_option"] == selected

    @staticmethod
    def option_text(question: aiosqlite.Row, letter: str) -> str:
        column = f"option_{letter.lower()}"
        return question[column]
