from __future__ import annotations

import logging
import random

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
from app.keyboards.main_menu import main_menu_kb
from app.keyboards.test_kb import answer_kb, next_question_kb, topic_choice_kb
from app.services.test_service import TestService
from app.states.test_states import QuizSG
from app.utils.texts import (
    BTN_MISTAKES,
    BTN_QUICK_START,
    BTN_TOPIC_TEST,
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
    """Готовит текст текущего вопроса с ПЕРЕМЕШАННЫМИ вариантами ответа.

    Сохраняет в FSM `option_map`: отображаемая буква → оригинальная буква в БД.
    Это убирает зависимость «правильный ответ всегда на одной позиции».
    """
    data = await state.get_data()
    question_ids: list[int] = data["question_ids"]
    current_index: int = data["current_index"]
    total = len(question_ids)
    question = await questions_repo.get(question_ids[current_index])
    if question is None:
        log.warning("Question %s not found", question_ids[current_index])
        return None

    originals = [
        ("A", question["option_a"]),
        ("B", question["option_b"]),
        ("C", question["option_c"]),
        ("D", question["option_d"]),
    ]
    random.shuffle(originals)
    option_map: dict[str, str] = {}
    display_options: dict[str, str] = {}
    for i, (orig_letter, opt_text) in enumerate(originals):
        disp = "ABCD"[i]
        option_map[disp] = orig_letter
        display_options[disp] = opt_text

    await state.update_data(
        current_question_id=question["id"],
        option_map=option_map,
    )
    text = (
        f"{question_header(current_index + 1, total, question['topic'])}\n\n"
        f"{question_body(question['text'], display_options)}"
    )
    return text, answer_kb()


async def _launch_test(
    answerable: Message,
    user_id: int,
    state: FSMContext,
    test_service: TestService,
    questions_repo: QuestionsRepo,
    questions: list,
    mode: str,
) -> None:
    """Создаёт попытку, прячет нижнюю клавиатуру и отправляет первый вопрос."""
    started = await test_service.start(user_id, mode, questions)
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
    await answerable.answer(
        f"Начинаю — {len(questions)} вопрос(ов).\n"
        "Чтобы прервать — кнопка «Прекратить тест» под вопросом.",
        reply_markup=ReplyKeyboardRemove(),
    )
    view = await _build_question_view(state, questions_repo)
    if view is None:
        await answerable.answer(
            "Не удалось начать тест: вопрос не найден.",
            reply_markup=main_menu_kb(),
        )
        await state.clear()
        return
    text, kb = view
    await answerable.answer(text, reply_markup=kb)


@router.message(F.text == BTN_QUICK_START)
async def start_quick(
    message: Message,
    state: FSMContext,
    questions_repo: QuestionsRepo,
    test_service: TestService,
) -> None:
    """Быстрый старт — 10 случайных вопросов из всех тем, без выбора темы."""
    if message.from_user is None:
        return
    questions = await test_service.pick_questions(message.from_user.id, "quick", None)
    if not questions:
        await message.answer(NO_QUESTIONS)
        return
    await _launch_test(
        message, message.from_user.id, state, test_service, questions_repo,
        questions, "quick",
    )


@router.message(F.text == BTN_MISTAKES)
async def start_mistakes(
    message: Message,
    state: FSMContext,
    questions_repo: QuestionsRepo,
    test_service: TestService,
) -> None:
    """Работа над ошибками — вопросы с последним неверным ответом пользователя."""
    if message.from_user is None:
        return
    questions = await test_service.pick_questions(
        message.from_user.id, "mistakes", None
    )
    if not questions:
        await message.answer(NO_MISTAKES)
        return
    await _launch_test(
        message, message.from_user.id, state, test_service, questions_repo,
        questions, "mistakes",
    )


@router.message(F.text == BTN_TOPIC_TEST)
async def start_topic_test(
    message: Message,
    state: FSMContext,
    questions_repo: QuestionsRepo,
) -> None:
    """Тест по теме — показать список тем для выбора."""
    if message.from_user is None:
        return
    topics = await questions_repo.list_topics_with_counts()
    if not topics:
        await message.answer(NO_QUESTIONS)
        return
    await state.set_state(QuizSG.choosing_topic)
    await state.update_data(topics=[t[0] for t in topics])
    await message.answer(
        "<b>Тест по теме</b>\nВыбери тему:",
        reply_markup=topic_choice_kb(topics),
    )


@router.callback_query(F.data == "topic:cancel", QuizSG.choosing_topic)
async def cancel_topic_choice(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    if callback.message is not None:
        try:
            await callback.message.edit_text("Выбор темы отменён.", reply_markup=None)
        except Exception:
            pass
    await callback.answer()


@router.callback_query(F.data.startswith("topic:"), QuizSG.choosing_topic)
async def on_topic_choice(
    callback: CallbackQuery,
    state: FSMContext,
    questions_repo: QuestionsRepo,
    test_service: TestService,
) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return

    selector = callback.data.split(":", 1)[1] if ":" in callback.data else ""
    data = await state.get_data()
    saved_topics: list[str] = data.get("topics", [])
    try:
        idx = int(selector)
    except ValueError:
        await callback.answer("Битый callback", show_alert=True)
        return
    if not (0 <= idx < len(saved_topics)):
        await callback.answer(
            "Тема не найдена, открой меню заново.", show_alert=True
        )
        return
    topic = saved_topics[idx]

    questions = await test_service.pick_questions(
        callback.from_user.id, "quick", topic
    )
    if not questions:
        try:
            await callback.message.edit_text(NO_QUESTIONS, reply_markup=None)
        except Exception:
            pass
        await state.clear()
        await callback.message.answer(
            "Возвращаюсь в меню.", reply_markup=main_menu_kb()
        )
        await callback.answer()
        return

    try:
        await callback.message.edit_text(
            f"<b>Тест по теме</b>\nТема: {topic}", reply_markup=None
        )
    except Exception:
        pass
    await _launch_test(
        callback.message, callback.from_user.id, state, test_service,
        questions_repo, questions, "quick",
    )
    await callback.answer()


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
    selected_display = callback.data.split(":", 1)[1]
    if selected_display not in {"A", "B", "C", "D"}:
        await callback.answer("Неизвестный вариант", show_alert=True)
        return

    data = await state.get_data()
    attempt_id: int = data["attempt_id"]
    question_ids: list[int] = data["question_ids"]
    current_index: int = data["current_index"]
    per_topic: dict = data.get("per_topic", {})
    option_map: dict = data.get("option_map", {})
    total = len(question_ids)

    question = await questions_repo.get(question_ids[current_index])
    if question is None:
        await callback.answer("Вопрос недоступен", show_alert=True)
        return

    # Отображаемая буква → оригинальная буква варианта в БД.
    selected_original = option_map.get(selected_display, selected_display)
    is_correct = question["correct_option"] == selected_original
    await events_repo.record(
        attempt_id=attempt_id,
        user_id=callback.from_user.id,
        question_id=question["id"],
        selected_option=selected_original,
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
    correct_original = question["correct_option"]
    correct_text = question[f"option_{correct_original.lower()}"]
    # Буква, под которой правильный ответ показан пользователю в этот раз.
    correct_display = next(
        (disp for disp, orig in option_map.items() if orig == correct_original),
        correct_original,
    )
    text = (
        f"{question_header(current_index + 1, total, topic)}\n\n"
        f"{explanation_text(is_correct, correct_display, correct_text, question['explanation'], question['law_reference'])}"
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
        await callback.message.answer(
            "Вернулся в главное меню.", reply_markup=main_menu_kb()
        )
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
    question_ids: list[int] = data["question_ids"]
    per_topic_raw: dict = data.get("per_topic", {})

    await attempts_repo.finish(attempt_id)
    attempt = await attempts_repo.get(attempt_id)
    correct = int(attempt["correct_count"]) if attempt else 0
    total = len(question_ids)

    per_topic = [
        (topic, vals[0], vals[1]) for topic, vals in sorted(per_topic_raw.items())
    ]

    text = summary_text(correct, total, per_topic)
    await state.clear()
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
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
