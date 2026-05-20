from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_main_kb(open_reports: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Статистика", callback_data="admin:stats")
    kb.button(text="Рассылка", callback_data="admin:broadcast")
    kb.button(text=f"Жалобы ({open_reports})", callback_data="admin:reports")
    kb.button(text="Закрыть", callback_data="admin:close")
    kb.adjust(1)
    return kb.as_markup()


def admin_back_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Назад в админку", callback_data="admin:main")
    return kb.as_markup()


def report_actions_kb(report_id: int, question_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Просмотрено", callback_data=f"rep:reviewed:{report_id}")
    kb.button(text="Исправлено", callback_data=f"rep:fixed:{report_id}")
    kb.button(text="Отклонить", callback_data=f"rep:rejected:{report_id}")
    kb.button(
        text="Деактивировать вопрос",
        callback_data=f"rep:deactivate:{report_id}:{question_id}",
    )
    kb.adjust(3, 1)
    return kb.as_markup()
