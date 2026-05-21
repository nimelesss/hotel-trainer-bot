from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def topic_choice_kb(topics: list[tuple[str, int]]) -> InlineKeyboardMarkup:
    """Inline-выбор темы: список тем с количеством вопросов + Отмена."""
    kb = InlineKeyboardBuilder()
    for idx, (topic, cnt) in enumerate(topics):
        kb.button(text=f"{topic} ({cnt})", callback_data=f"topic:{idx}")
    kb.button(text="Отмена", callback_data="topic:cancel")
    kb.adjust(1)
    return kb.as_markup()


def answer_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for letter in ("A", "B", "C", "D"):
        kb.button(text=letter, callback_data=f"answer:{letter}")
    kb.button(text="Сообщить об ошибке", callback_data="report:current")
    kb.button(text="Прекратить тест", callback_data="quiz:cancel")
    kb.adjust(4, 1, 1)
    return kb.as_markup()


def next_question_kb(is_last: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if is_last:
        kb.button(text="Завершить", callback_data="quiz:finish")
    else:
        kb.button(text="Дальше", callback_data="quiz:next")
    kb.button(text="Сообщить об ошибке", callback_data="report:current")
    kb.adjust(1)
    return kb.as_markup()
