from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.games import router as games_router
from app.api.v1.admin import router as admin_router
__all__ = ["auth_router", "users_router", "games_router", "admin_router"]