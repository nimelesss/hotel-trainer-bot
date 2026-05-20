from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import Message

from app.services.stats_service import StatsService
from app.utils.texts import BTN_STATS, stats_user_text

log = logging.getLogger(__name__)
router = Router(name="stats")


@router.message(F.text == BTN_STATS)
async def show_my_stats(
    message: Message,
    stats_service: StatsService,
) -> None:
    if message.from_user is None:
        return
    stats = await stats_service.user_stats(message.from_user.id)
    text = stats_user_text(stats.correct, stats.total, stats.per_topic)
    await message.answer(text)
