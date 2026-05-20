from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.db.repositories.reports_repo import ReportsRepo
from app.utils.texts import REPORT_THANKS

log = logging.getLogger(__name__)
router = Router(name="report")


@router.callback_query(F.data == "report:current")
async def report_current_question(
    callback: CallbackQuery,
    state: FSMContext,
    reports_repo: ReportsRepo,
) -> None:
    if callback.from_user is None:
        await callback.answer()
        return
    data = await state.get_data()
    question_id = data.get("current_question_id")
    if not question_id:
        await callback.answer(
            "Нет текущего вопроса для жалобы.", show_alert=True
        )
        return
    try:
        await reports_repo.create(
            user_id=callback.from_user.id,
            question_id=int(question_id),
        )
    except Exception as e:
        log.warning(
            "Failed to create report for user %s, question %s: %s",
            callback.from_user.id, question_id, e,
        )
        await callback.answer(
            "Не получилось сохранить жалобу. Попробуй ещё раз.",
            show_alert=True,
        )
        return
    await callback.answer(REPORT_THANKS, show_alert=False)
