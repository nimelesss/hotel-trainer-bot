from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.db.repositories.attempts_repo import AttemptsRepo
from app.keyboards.main_menu import main_menu_kb
from app.utils.texts import CANCELLED, HELP, MAIN_MENU_TITLE, welcome

log = logging.getLogger(__name__)
router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    state: FSMContext,
    attempts_repo: AttemptsRepo,
    law_base_date: str,
) -> None:
    user = message.from_user
    if user is None:
        return
    await state.clear()
    await attempts_repo.abandon_active_for_user(user.id)
    name = user.first_name or "коллега"
    await message.answer(welcome(name, law_base_date))
    await message.answer(MAIN_MENU_TITLE, reply_markup=main_menu_kb())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP)


@router.message(Command("cancel"))
async def cmd_cancel(
    message: Message,
    state: FSMContext,
    attempts_repo: AttemptsRepo,
) -> None:
    if message.from_user is None:
        return
    await state.clear()
    await attempts_repo.abandon_active_for_user(message.from_user.id)
    await message.answer(CANCELLED, reply_markup=main_menu_kb())
