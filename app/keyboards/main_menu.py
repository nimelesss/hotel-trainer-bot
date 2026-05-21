from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from app.utils.texts import (
    BTN_ABOUT,
    BTN_MISTAKES,
    BTN_QUICK_START,
    BTN_STATS,
    BTN_TOPIC_TEST,
)


def main_menu_kb() -> ReplyKeyboardMarkup:
    """Постоянная reply-клавиатура с главным меню, всегда видна внизу чата."""
    kb = ReplyKeyboardBuilder()
    kb.button(text=BTN_QUICK_START)
    kb.button(text=BTN_TOPIC_TEST)
    kb.button(text=BTN_MISTAKES)
    kb.button(text=BTN_STATS)
    kb.button(text=BTN_ABOUT)
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True, is_persistent=True)
