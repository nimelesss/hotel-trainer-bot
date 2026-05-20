from __future__ import annotations

QUICK_TEST_SIZE = 10
EXAM_SIZE = 50
MISTAKES_SIZE = 10


def disclaimer(date: str) -> str:
    return (
        f"<i>База актуальна на: <b>{date}</b>. "
        "Тесты учебные и не являются юридической консультацией.</i>"
    )


def welcome(name: str, date: str) -> str:
    return (
        f"Привет, <b>{name}</b>!\n\n"
        "Это тренажёр для персонала гостиниц по законам РФ "
        "о туризме и гостеприимстве.\n\n"
        f"{disclaimer(date)}\n\n"
        "Выбери режим в меню ниже."
    )


HELP = (
    "Команды:\n"
    "/start — главное меню\n"
    "/help — эта подсказка\n"
    "/cancel — выйти из текущего теста"
)

MAIN_MENU_TITLE = "Главное меню. Выбери режим:"

MODE_LABELS = {
    "quick": f"Быстрый тест ({QUICK_TEST_SIZE} вопросов)",
    "exam": f"Экзамен ({EXAM_SIZE} вопросов)",
    "mistakes": f"Работа над ошибками (до {MISTAKES_SIZE})",
}


def question_header(index: int, total: int, topic: str) -> str:
    return f"<b>Вопрос {index}/{total}</b>  ·  <i>{topic}</i>"


def question_body(text: str, options: dict[str, str]) -> str:
    return (
        f"{text}\n\n"
        f"<b>A.</b> {options['A']}\n"
        f"<b>B.</b> {options['B']}\n"
        f"<b>C.</b> {options['C']}\n"
        f"<b>D.</b> {options['D']}"
    )


def explanation_text(
    is_correct: bool,
    correct_option: str,
    correct_text: str,
    explanation: str | None,
    law_reference: str | None,
) -> str:
    head = "✅ Верно!" if is_correct else "❌ Неверно."
    lines = [head, f"Правильный ответ: <b>{correct_option}</b>. {correct_text}"]
    if explanation:
        lines.append("")
        lines.append(f"<b>Разбор:</b> {explanation}")
    if law_reference:
        lines.append(f"<b>Норма права:</b> {law_reference}")
    return "\n".join(lines)


def summary_text(
    mode: str,
    correct: int,
    total: int,
    per_topic: list[tuple[str, int, int]],
) -> str:
    mode_label = MODE_LABELS.get(mode, mode)
    percent = (correct / total * 100) if total else 0
    lines = [
        f"<b>Тест завершён</b>: {mode_label}",
        f"Результат: <b>{correct} из {total}</b> ({percent:.0f}%)",
    ]
    if per_topic:
        lines.append("")
        lines.append("<b>По темам этого теста:</b>")
        for topic, topic_correct, topic_total in per_topic:
            lines.append(f"• {topic}: {topic_correct}/{topic_total}")
    return "\n".join(lines)


NO_MISTAKES = (
    "У тебя пока нет ошибок 🎉\n"
    "Сначала пройди быстрый тест или экзамен — потом сможешь поработать над ошибками."
)

NO_QUESTIONS = (
    "В базе пока нет активных вопросов. "
    "Подожди, пока администратор загрузит вопросы."
)

REPORT_THANKS = "Спасибо! Жалоба отправлена администратору."
ALREADY_REPORTED = "Ты уже отправил жалобу по этому вопросу. Спасибо!"

CANCELLED = "Тест прекращён. Возвращаемся в главное меню."

ABOUT = (
    "<b>О боте</b>\n\n"
    "Этот бот — тренажёр для персонала гостиниц по законам РФ "
    "о туризме и гостеприимстве.\n\n"
    "<b>Режимы:</b>\n"
    "• Быстрый тест — 10 случайных вопросов.\n"
    "• Экзамен — 50 случайных вопросов.\n"
    "• Работа над ошибками — вопросы, в которых ты ошибался "
    "(уйдут из списка, как только ответишь правильно).\n\n"
    "Под каждым вопросом есть кнопка «Сообщить об ошибке» — "
    "если нашёл опечатку или неточность, жми."
)


def stats_user_text(
    total_attempts_correct: int,
    total_attempts: int,
    per_topic: list[tuple[str, int, int]],
) -> str:
    if total_attempts == 0:
        return (
            "<b>Твоя статистика</b>\n\n"
            "Ты ещё не отвечал ни на один вопрос. "
            "Пройди быстрый тест, чтобы увидеть результаты."
        )
    percent = total_attempts_correct / total_attempts * 100
    lines = [
        "<b>Твоя статистика</b>",
        f"Всего ответов: <b>{total_attempts}</b>",
        f"Верных: <b>{total_attempts_correct}</b> ({percent:.0f}%)",
    ]
    if per_topic:
        lines.append("")
        lines.append("<b>По темам:</b>")
        for topic, correct, total in per_topic:
            t_pct = correct / total * 100 if total else 0
            lines.append(f"• {topic}: {correct}/{total} ({t_pct:.0f}%)")
    return "\n".join(lines)


def admin_stats_text(
    users_total: int,
    questions_active: int,
    attempts_today: int,
    reports_open: int,
) -> str:
    return (
        "<b>Админ-статистика</b>\n\n"
        f"Пользователей: <b>{users_total}</b>\n"
        f"Активных вопросов: <b>{questions_active}</b>\n"
        f"Завершённых тестов сегодня: <b>{attempts_today}</b>\n"
        f"Открытых жалоб: <b>{reports_open}</b>"
    )


BROADCAST_PROMPT = (
    "Пришли текст рассылки одним сообщением. "
    "Можно использовать HTML-форматирование.\n\n"
    "Чтобы отменить — /cancel."
)

BROADCAST_CANCELLED = "Рассылка отменена."


def broadcast_done(sent: int, failed: int) -> str:
    return (
        f"Рассылка завершена.\n"
        f"Отправлено: <b>{sent}</b>\n"
        f"Не доставлено: <b>{failed}</b>"
    )


REPORTS_EMPTY = "Открытых жалоб нет."

ADMIN_ONLY = "Эта команда доступна только администратору."


def report_card(
    report_id: int,
    question_id: int,
    topic: str,
    question_text: str,
    user_id: int,
    comment: str | None,
    created_at: str,
) -> str:
    lines = [
        f"<b>Жалоба #{report_id}</b>",
        f"<b>От:</b> <code>{user_id}</code>",
        f"<b>Когда:</b> {created_at}",
        f"<b>Вопрос #{question_id}</b> ({topic}):",
        f"<i>{question_text}</i>",
    ]
    if comment:
        lines.append("")
        lines.append(f"<b>Комментарий:</b> {comment}")
    return "\n".join(lines)
