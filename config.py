from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_id: int
    db_path: Path
    seed_path: Path
    law_base_date: str
    log_level: str
    proxy_url: str | None

    @classmethod
    def load(cls, env_file: str | None = None) -> "Config":
        load_dotenv(env_file)

        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        if not bot_token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is empty. Fill it in .env")

        admin_raw = os.getenv("ADMIN_TELEGRAM_ID", "").strip()
        if not admin_raw.isdigit():
            raise RuntimeError(
                "ADMIN_TELEGRAM_ID must be a positive integer. Got: "
                f"{admin_raw!r}"
            )
        admin_id = int(admin_raw)

        db_path = Path(os.getenv("DB_PATH", "data/bot.db"))
        seed_path = Path(os.getenv("SEED_QUESTIONS_PATH", "data/questions_seed.json"))
        law_base_date = os.getenv("LAW_BASE_DATE", "—").strip() or "—"
        log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()
        if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            log_level = "INFO"

        proxy_url = os.getenv("PROXY_URL", "").strip() or None

        return cls(
            bot_token=bot_token,
            admin_id=admin_id,
            db_path=db_path,
            seed_path=seed_path,
            law_base_date=law_base_date,
            log_level=log_level,
            proxy_url=proxy_url,
        )


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
