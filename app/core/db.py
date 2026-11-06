from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import Settings

settings = Settings()

engine = create_async_engine(
    settings.database_url,
    echo=False,
)

session_factory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False
)

async def get_db():
    async with session_factory() as s:
        yield s

