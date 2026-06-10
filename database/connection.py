from pathlib import Path
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

from config.settings import settings


engine = create_engine(
    f"sqlite:///{settings.database_path}",
    echo=settings.database_echo,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("PRAGMA journal_mode = WAL")
    cursor.execute("PRAGMA synchronous = NORMAL")
    cursor.close()


@contextmanager
def get_session() -> Session:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    from database.seed import create_tables, seed_data
    create_tables(engine)
    seed_data(engine)


def execute_read_only(sql: str, params: dict | None = None):
    with engine.connect() as conn:
        conn.execute(text("PRAGMA query_only = ON"))
        result = conn.execute(text(sql), params or {})
        return result.fetchall(), result.keys()