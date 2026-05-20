from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import Message

from app.utils.texts import ABOUT, BTN_ABOUT

log = logging.getLogger(__name__)
router = Router(name="menu")


@router.message(F.text == BTN_ABOUT)
async def show_about(message: Message) -> None:
    await message.answer(ABOUT)
