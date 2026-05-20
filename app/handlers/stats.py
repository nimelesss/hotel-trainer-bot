from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.keyboards.main_menu import back_to_menu_kb
from app.services.stats_service import StatsService
from app.utils.texts import stats_user_text

log = logging.getLogger(__name__)
router = Router(name="stats")


@router.callback_query(F.data == "stats:me")
async def show_my_stats(
    callback: CallbackQuery,
    stats_service: StatsService,
) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    stats = await stats_service.user_stats(callback.from_user.id)
    text = stats_user_text(stats.correct, stats.total, stats.per_topic)
    try:
        await callback.message.edit_text(text, reply_markup=back_to_menu_kb())
    except Exception:
        await callback.message.answer(text, reply_markup=back_to_menu_kb())
    await callback.answer()
