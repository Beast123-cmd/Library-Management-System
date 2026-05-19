from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Convert postgresql:// -> postgresql+asyncpg:// for async driver
db_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Clean up query parameters that asyncpg doesn't support
if "?" in db_url:
    base_url, query = db_url.split("?", 1)
    params = query.split("&")
    clean_params = [p for p in params if not p.startswith("sslmode") and not p.startswith("channel_binding")]
    if clean_params:
        db_url = base_url + "?" + "&".join(clean_params)
    else:
        db_url = base_url

engine = create_async_engine(
    db_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,   # Healthcheck connections before use
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency that provides a scoped async DB session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
