import os
from datetime import timedelta

DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./chess_platform.db")
SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production-please")
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRE_DAYS: int = int(os.getenv("SESSION_DAYS", "7"))
MAX_STEP_MINUTES: int = int(os.getenv("MAX_STEP_MINUTES", "5"))
TEMP_CREDENTIAL_MAX_DAYS: int = 15
TEMP_CREDENTIAL_DEFAULT_DAYS: int = 3
LOGIN_RATE_LIMIT: str = "5/minute"
DEBUG_COOLDOWN_HOURS: int = 24
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8000"))
LOAD_PAGES: list[dict] = [
    {"id": "page1", "text": "欢迎登录，{username}"},
    {"id": "page2", "text": "棋局万变，心境如一"},
    {"id": "page3", "text": "正在准备环境..."},
]
JWT_ACCESS_TOKEN_EXPIRE: timedelta = timedelta(days=JWT_EXPIRE_DAYS)
