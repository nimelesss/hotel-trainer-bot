from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.db.repositories.attempts_repo import AttemptsRepo
from app.keyboards.main_menu import back_to_menu_kb, main_menu_kb
from app.utils.texts import ABOUT, MAIN_MENU_TITLE

log = logging.getLogger(__name__)
router = Router(name="menu")


@router.callback_query(F.data == "menu:main")
async def show_main_menu(
    callback: CallbackQuery,
    state: FSMContext,
    attempts_repo: AttemptsRepo,
) -> None:
    await state.clear()
    if callback.from_user:
        await attempts_repo.abandon_active_for_user(callback.from_user.id)
    if isinstance(callback.message, type(None)):
        await callback.answer()
        return
    try:
        await callback.message.edit_text(
            MAIN_MENU_TITLE, reply_markup=main_menu_kb()
        )
    except Exception:
        await callback.message.answer(MAIN_MENU_TITLE, reply_markup=main_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "info:about")
async def show_about(callback: CallbackQuery) -> None:
    if callback.message is None:
        await callback.answer()
        return
    try:
        await callback.message.edit_text(ABOUT, reply_markup=back_to_menu_kb())
    except Exception:
        await callback.message.answer(ABOUT, reply_markup=back_to_menu_kb())
    await callback.answer()
