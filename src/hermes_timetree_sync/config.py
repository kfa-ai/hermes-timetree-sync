from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    timetree_base_url: str = "https://timetreeapp.com"
    timetree_session_cookie: str | None = None
    timetree_email: str | None = None
    timetree_password: str | None = None
    timetree_calendar_id: str | None = None


def load_settings() -> Settings:
    load_dotenv()
    return Settings(
        timetree_session_cookie=os.getenv("TIMETREE_SESSION_COOKIE"),
        timetree_email=os.getenv("TIMETREE_EMAIL"),
        timetree_password=os.getenv("TIMETREE_PASSWORD"),
        timetree_calendar_id=os.getenv("TIMETREE_CALENDAR_ID"),
    )
