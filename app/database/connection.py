from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app import config

engine = create_async_engine(config.DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def init_db() -> None:
    import app.models.user
    import app.models.game
    import app.models.system
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
