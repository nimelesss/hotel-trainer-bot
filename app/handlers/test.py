from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardRemove,
)

from app.db.repositories.attempts_repo import AttemptsRepo
from app.db.repositories.events_repo import EventsRepo
from app.db.repositories.questions_repo import QuestionsRepo
from app.keyboards.main_menu import MODE_BY_BUTTON, main_menu_kb
from app.keyboards.test_kb import answer_kb, next_question_kb
from app.services.test_service import TestService
from app.states.test_states import QuizSG
from app.utils.texts import (
    CANCELLED,
    NO_MISTAKES,
    NO_QUESTIONS,
    explanation_text,
    question_body,
    question_header,
    summary_text,
)

log = logging.getLogger(__name__)
router = Router(name="test")


async def _build_question_view(
    state: FSMContext,
    questions_repo: QuestionsRepo,
) -> tuple[str, InlineKeyboardMarkup] | None:
    data = await state.get_data()
    question_ids: list[int] = data["question_ids"]
    current_index: int = data["current_index"]
    total = len(question_ids)
    question = await questions_repo.get(question_ids[current_index])
    if question is None:
        log.warning("Question %s not found", question_ids[current_index])
        return None
    await state.update_data(current_question_id=question["id"])
    options = {
        "A": question["option_a"],
        "B": question["option_b"],
        "C": question["option_c"],
        "D": question["option_d"],
    }
    text = (
        f"{question_header(current_index + 1, total, question['topic'])}\n\n"
        f"{question_body(question['text'], options)}"
    )
    return text, answer_kb()


@router.message(F.text.in_(MODE_BY_BUTTON))
async def start_test_via_button(
    message: Message,
    state: FSMContext,
    questions_repo: QuestionsRepo,
    test_service: TestService,
) -> None:
    if message.from_user is None:
        return
    mode = MODE_BY_BUTTON[message.text]
    questions = await test_service.pick_questions(message.from_user.id, mode)
    if not questions:
        text = NO_MISTAKES if mode == "mistakes" else NO_QUESTIONS
        await message.answer(text)
        return
    started = await test_service.start(message.from_user.id, mode, questions)
    await state.set_state(QuizSG.in_progress)
    await state.set_data(
        {
            "attempt_id": started.attempt_id,
            "question_ids": started.question_ids,
            "current_index": 0,
            "mode": mode,
            "per_topic": {},
        }
    )
    # Скрываем нижнюю клавиатуру на время теста, чтобы случайно не сбить прогресс.
    # Возвращается в finish_test / cancel_test / cmd_cancel.
    await message.answer(
        f"Начинаю: {message.text}.\n"
        "Чтобы прервать — кнопка «Прекратить тест» под вопросом.",
        reply_markup=ReplyKeyboardRemove(),
    )
    view = await _build_question_view(state, questions_repo)
    if view is None:
        await message.answer(
            "Не удалось начать тест: вопрос не найден.",
            reply_markup=main_menu_kb(),
        )
        await state.clear()
        return
    text, kb = view
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("answer:"), QuizSG.in_progress)
async def on_answer(
    callback: CallbackQuery,
    state: FSMContext,
    questions_repo: QuestionsRepo,
    attempts_repo: AttemptsRepo,
    events_repo: EventsRepo,
) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    selected = callback.data.split(":", 1)[1]
    if selected not in {"A", "B", "C", "D"}:
        await callback.answer("Неизвестный вариант", show_alert=True)
        return

    data = await state.get_data()
    attempt_id: int = data["attempt_id"]
    question_ids: list[int] = data["question_ids"]
    current_index: int = data["current_index"]
    per_topic: dict = data.get("per_topic", {})
    total = len(question_ids)

    question = await questions_repo.get(question_ids[current_index])
    if question is None:
        await callback.answer("Вопрос недоступен", show_alert=True)
        return

    is_correct = question["correct_option"] == selected
    await events_repo.record(
        attempt_id=attempt_id,
        user_id=callback.from_user.id,
        question_id=question["id"],
        selected_option=selected,
        is_correct=is_correct,
    )
    if is_correct:
        await attempts_repo.increment_correct(attempt_id)

    topic = question["topic"]
    bucket = per_topic.setdefault(topic, [0, 0])
    bucket[1] += 1
    if is_correct:
        bucket[0] += 1

    new_index = current_index + 1
    is_last = new_index >= total
    correct_letter = question["correct_option"]
    correct_text = question[f"option_{correct_letter.lower()}"]
    text = (
        f"{question_header(current_index + 1, total, topic)}\n\n"
        f"{explanation_text(is_correct, correct_letter, correct_text, question['explanation'], question['law_reference'])}"
    )

    await state.update_data(
        current_index=new_index,
        current_question_id=question["id"],
        per_topic=per_topic,
    )
    await state.set_state(QuizSG.viewing_explanation)
    try:
        await callback.message.edit_text(text, reply_markup=next_question_kb(is_last))
    except Exception:
        await callback.message.answer(text, reply_markup=next_question_kb(is_last))
    await callback.answer()


@router.callback_query(F.data == "quiz:next", QuizSG.viewing_explanation)
async def next_question(
    callback: CallbackQuery,
    state: FSMContext,
    questions_repo: QuestionsRepo,
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    view = await _build_question_view(state, questions_repo)
    if view is None:
        try:
            await callback.message.edit_text("Вопрос недоступен.", reply_markup=None)
        except Exception:
            pass
        await state.clear()
        await callback.message.answer("Вернулся в главное меню.", reply_markup=main_menu_kb())
        await callback.answer()
        return
    text, kb = view
    await state.set_state(QuizSG.in_progress)
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        await callback.message.answer(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "quiz:finish", QuizSG.viewing_explanation)
async def finish_test(
    callback: CallbackQuery,
    state: FSMContext,
    attempts_repo: AttemptsRepo,
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    data = await state.get_data()
    attempt_id: int = data["attempt_id"]
    mode: str = data.get("mode", "quick")
    question_ids: list[int] = data["question_ids"]
    per_topic_raw: dict = data.get("per_topic", {})

    await attempts_repo.finish(attempt_id)
    attempt = await attempts_repo.get(attempt_id)
    correct = int(attempt["correct_count"]) if attempt else 0
    total = len(question_ids)

    per_topic = [
        (topic, vals[0], vals[1]) for topic, vals in sorted(per_topic_raw.items())
    ]

    text = summary_text(mode, correct, total, per_topic)
    await state.clear()
    # Убираем inline-кнопки с последнего разбора, текст оставляем.
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    # Итог + возвращаем нижнюю клавиатуру.
    await callback.message.answer(text, reply_markup=main_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "quiz:cancel")
async def cancel_test(
    callback: CallbackQuery,
    state: FSMContext,
    attempts_repo: AttemptsRepo,
) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    await attempts_repo.abandon_active_for_user(callback.from_user.id)
    await state.clear()
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await callback.message.answer(CANCELLED, reply_markup=main_menu_kb())
    await callback.answer()
