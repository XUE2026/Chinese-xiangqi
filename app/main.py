import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1 import admin_router, auth_router, games_router, users_router


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    from app.database.connection import init_db
    await init_db()
    yield


fastapi_app = FastAPI(title="Chess Platform API", lifespan=lifespan)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(_static_dir, exist_ok=True)
fastapi_app.mount("/static", StaticFiles(directory=_static_dir), name="static")

fastapi_app.include_router(auth_router)
fastapi_app.include_router(users_router)
fastapi_app.include_router(games_router)
fastapi_app.include_router(admin_router)

limiter = Limiter(key_func=get_remote_address)
fastapi_app.state.limiter = limiter
fastapi_app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

from app.api.websocket.game_socket import init_socketio

init_socketio(sio)

app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)