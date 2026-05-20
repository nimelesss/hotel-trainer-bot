from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from app.utils.texts import BTN_ABOUT, BTN_STATS, MODE_LABELS

# Маппинг текста кнопки → режим теста. Используется text-хэндлером.
MODE_BY_BUTTON: dict[str, str] = {
    MODE_LABELS["quick"]: "quick",
    MODE_LABELS["exam"]: "exam",
    MODE_LABELS["mistakes"]: "mistakes",
}


def main_menu_kb() -> ReplyKeyboardMarkup:
    """Постоянная reply-клавиатура с главным меню, всегда видна внизу чата."""
    kb = ReplyKeyboardBuilder()
    kb.button(text=MODE_LABELS["quick"])
    kb.button(text=MODE_LABELS["exam"])
    kb.button(text=MODE_LABELS["mistakes"])
    kb.button(text=BTN_STATS)
    kb.button(text=BTN_ABOUT)
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True, is_persistent=True)
