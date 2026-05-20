from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.db.repositories.questions_repo import QuestionsRepo
from app.db.repositories.reports_repo import ReportsRepo
from app.db.repositories.users_repo import UsersRepo
from app.keyboards.admin_kb import admin_back_kb, admin_main_kb, report_actions_kb
from app.services.stats_service import StatsService
from app.states.test_states import AdminSG
from app.utils.texts import (
    ADMIN_ONLY,
    BROADCAST_CANCELLED,
    BROADCAST_PROMPT,
    REPORTS_EMPTY,
    admin_stats_text,
    broadcast_done,
    report_card,
)

log = logging.getLogger(__name__)
router = Router(name="admin")

BROADCAST_DELAY_SEC = 0.04  # ~25 сообщений в секунду, чтобы не упереться в лимиты Telegram


def _is_admin(user_id: int | None, admin_id: int) -> bool:
    return user_id is not None and user_id == admin_id


async def _show_admin_menu(
    message_or_cb: Message | CallbackQuery,
    reports_repo: ReportsRepo,
) -> None:
    open_count = await reports_repo.count_open()
    text = "<b>Админ-панель</b>"
    kb = admin_main_kb(open_count)
    if isinstance(message_or_cb, CallbackQuery):
        if message_or_cb.message is None:
            return
        try:
            await message_or_cb.message.edit_text(text, reply_markup=kb)
        except Exception:
            await message_or_cb.message.answer(text, reply_markup=kb)
    else:
        await message_or_cb.answer(text, reply_markup=kb)


@router.message(Command("admin"))
async def cmd_admin(
    message: Message,
    state: FSMContext,
    admin_id: int,
    reports_repo: ReportsRepo,
) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None, admin_id):
        await message.answer(ADMIN_ONLY)
        return
    await state.clear()
    await _show_admin_menu(message, reports_repo)


@router.callback_query(F.data == "admin:main")
async def cb_admin_main(
    callback: CallbackQuery,
    state: FSMContext,
    admin_id: int,
    reports_repo: ReportsRepo,
) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else None, admin_id):
        await callback.answer(ADMIN_ONLY, show_alert=True)
        return
    await state.clear()
    await _show_admin_menu(callback, reports_repo)
    await callback.answer()


@router.callback_query(F.data == "admin:stats")
async def cb_admin_stats(
    callback: CallbackQuery,
    admin_id: int,
    stats_service: StatsService,
) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else None, admin_id):
        await callback.answer(ADMIN_ONLY, show_alert=True)
        return
    if callback.message is None:
        await callback.answer()
        return
    stats = await stats_service.admin_stats()
    text = admin_stats_text(
        users_total=stats.users_total,
        questions_active=stats.questions_active,
        attempts_today=stats.attempts_today,
        reports_open=stats.reports_open,
    )
    try:
        await callback.message.edit_text(text, reply_markup=admin_back_kb())
    except Exception:
        await callback.message.answer(text, reply_markup=admin_back_kb())
    await callback.answer()


@router.callback_query(F.data == "admin:close")
async def cb_admin_close(callback: CallbackQuery) -> None:
    if callback.message is None:
        await callback.answer()
        return
    try:
        await callback.message.edit_text("Админ-панель закрыта.")
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == "admin:broadcast")
async def cb_admin_broadcast_start(
    callback: CallbackQuery,
    state: FSMContext,
    admin_id: int,
) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else None, admin_id):
        await callback.answer(ADMIN_ONLY, show_alert=True)
        return
    if callback.message is None:
        await callback.answer()
        return
    await state.set_state(AdminSG.broadcasting)
    try:
        await callback.message.edit_text(BROADCAST_PROMPT, reply_markup=admin_back_kb())
    except Exception:
        await callback.message.answer(BROADCAST_PROMPT, reply_markup=admin_back_kb())
    await callback.answer()


@router.message(AdminSG.broadcasting, Command("cancel"))
async def broadcast_cancel(
    message: Message,
    state: FSMContext,
    reports_repo: ReportsRepo,
) -> None:
    await state.clear()
    await message.answer(BROADCAST_CANCELLED)
    await _show_admin_menu(message, reports_repo)


@router.message(AdminSG.broadcasting)
async def broadcast_send(
    message: Message,
    state: FSMContext,
    bot: Bot,
    admin_id: int,
    users_repo: UsersRepo,
    reports_repo: ReportsRepo,
) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None, admin_id):
        return
    text = message.html_text if message.text else None
    if not text:
        await message.answer("Я могу разослать только текст. Пришли текстовое сообщение или /cancel.")
        return

    user_ids = await users_repo.all_active_ids()
    sent = 0
    failed = 0
    progress = await message.answer(f"Рассылка начата. Получателей: {len(user_ids)}…")

    for uid in user_ids:
        try:
            await bot.send_message(uid, text)
            sent += 1
        except TelegramForbiddenError:
            failed += 1
            try:
                await users_repo.mark_blocked(uid, True)
            except Exception:
                pass
        except TelegramRetryAfter as e:
            log.warning("Broadcast rate-limited: retry after %s sec", e.retry_after)
            await asyncio.sleep(e.retry_after + 1)
            try:
                await bot.send_message(uid, text)
                sent += 1
            except Exception as inner:
                log.warning("Broadcast retry failed for %s: %s", uid, inner)
                failed += 1
        except Exception as e:
            log.warning("Broadcast failed for %s: %s", uid, e)
            failed += 1
        await asyncio.sleep(BROADCAST_DELAY_SEC)

    await state.clear()
    try:
        await progress.edit_text(broadcast_done(sent, failed))
    except Exception:
        await message.answer(broadcast_done(sent, failed))
    await _show_admin_menu(message, reports_repo)


@router.callback_query(F.data == "admin:reports")
async def cb_admin_reports(
    callback: CallbackQuery,
    admin_id: int,
    reports_repo: ReportsRepo,
) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else None, admin_id):
        await callback.answer(ADMIN_ONLY, show_alert=True)
        return
    if callback.message is None:
        await callback.answer()
        return
    reports = await reports_repo.list_open(limit=10)
    if not reports:
        try:
            await callback.message.edit_text(REPORTS_EMPTY, reply_markup=admin_back_kb())
        except Exception:
            await callback.message.answer(REPORTS_EMPTY, reply_markup=admin_back_kb())
        await callback.answer()
        return

    try:
        await callback.message.edit_text(
            f"Открытых жалоб: {len(reports)}. Каждая ниже отдельным сообщением.",
            reply_markup=admin_back_kb(),
        )
    except Exception:
        pass

    for row in reports:
        text = report_card(
            report_id=row["id"],
            question_id=row["question_id"],
            topic=row["topic"],
            question_text=row["text"],
            user_id=row["user_id"],
            comment=row["comment"],
            created_at=str(row["created_at"]),
        )
        await callback.message.answer(
            text, reply_markup=report_actions_kb(row["id"], row["question_id"])
        )
    await callback.answer()


@router.callback_query(F.data.startswith("rep:"))
async def cb_report_action(
    callback: CallbackQuery,
    admin_id: int,
    reports_repo: ReportsRepo,
    questions_repo: QuestionsRepo,
) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else None, admin_id):
        await callback.answer(ADMIN_ONLY, show_alert=True)
        return
    if callback.message is None:
        await callback.answer()
        return
    parts = callback.data.split(":")
    action = parts[1]
    try:
        report_id = int(parts[2])
    except (IndexError, ValueError):
        await callback.answer("Битый callback", show_alert=True)
        return

    if action == "deactivate":
        try:
            question_id = int(parts[3])
        except (IndexError, ValueError):
            await callback.answer("Битый callback", show_alert=True)
            return
        await questions_repo.set_active(question_id, False)
        await reports_repo.update_status(report_id, "fixed", admin_note="question deactivated")
        suffix = "✓ Вопрос деактивирован, жалоба закрыта"
    elif action in {"reviewed", "fixed", "rejected"}:
        await reports_repo.update_status(report_id, action)
        suffix = f"✓ Статус жалобы: {action}"
    else:
        await callback.answer("Неизвестное действие", show_alert=True)
        return

    try:
        original = callback.message.html_text or callback.message.text or ""
        await callback.message.edit_text(f"{original}\n\n<b>{suffix}</b>")
    except Exception:
        await callback.message.answer(suffix)
    await callback.answer()
