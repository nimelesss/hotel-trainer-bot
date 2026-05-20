from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.utils.texts import MODE_LABELS


def main_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=MODE_LABELS["quick"], callback_data="mode:quick")
    kb.button(text=MODE_LABELS["exam"], callback_data="mode:exam")
    kb.button(text=MODE_LABELS["mistakes"], callback_data="mode:mistakes")
    kb.button(text="Моя статистика", callback_data="stats:me")
    kb.button(text="О боте", callback_data="info:about")
    kb.adjust(1)
    return kb.as_markup()


def back_to_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="В главное меню", callback_data="menu:main")
    return kb.as_markup()
