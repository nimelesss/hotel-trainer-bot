from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.db.connection import Database
from app.db.init_db import init_database
from app.db.repositories.attempts_repo import AttemptsRepo
from app.db.repositories.events_repo import EventsRepo
from app.db.repositories.questions_repo import QuestionsRepo
from app.db.repositories.reports_repo import ReportsRepo
from app.db.repositories.users_repo import UsersRepo
from app.handlers import admin, menu, report, start, stats, test
from app.middlewares.user_middleware import UserMiddleware
from app.services.stats_service import StatsService
from app.services.test_service import TestService
from config import Config, setup_logging

log = logging.getLogger(__name__)


async def main() -> None:
    config = Config.load()
    setup_logging(config.log_level)
    log.info("Starting bot…")

    db = Database(config.db_path)
    await db.connect()
    try:
        await init_database(db, seed_path=config.seed_path)

        users_repo = UsersRepo(db)
        questions_repo = QuestionsRepo(db)
        attempts_repo = AttemptsRepo(db)
        events_repo = EventsRepo(db)
        reports_repo = ReportsRepo(db)

        test_service = TestService(questions_repo, attempts_repo)
        stats_service = StatsService(
            users_repo, events_repo, questions_repo, attempts_repo, reports_repo
        )

        session = AiohttpSession(proxy=config.proxy_url) if config.proxy_url else None
        if config.proxy_url:
            log.info("Using HTTPS proxy for Telegram API")
        bot = Bot(
            config.bot_token,
            session=session,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        dp = Dispatcher(storage=MemoryStorage())

        dp["users_repo"] = users_repo
        dp["questions_repo"] = questions_repo
        dp["attempts_repo"] = attempts_repo
        dp["events_repo"] = events_repo
        dp["reports_repo"] = reports_repo
        dp["test_service"] = test_service
        dp["stats_service"] = stats_service
        dp["admin_id"] = config.admin_id
        dp["law_base_date"] = config.law_base_date

        dp.update.outer_middleware(UserMiddleware(users_repo))

        dp.include_router(start.router)
        dp.include_router(admin.router)
        dp.include_router(menu.router)
        dp.include_router(test.router)
        dp.include_router(stats.router)
        dp.include_router(report.router)

        try:
            await bot.delete_webhook(drop_pending_updates=True)
            me = await bot.get_me()
            log.info("Polling started as @%s (id=%s)", me.username, me.id)
            await dp.start_polling(bot)
        finally:
            await bot.session.close()
    finally:
        await db.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.getLogger(__name__).info("Stopped by signal")
