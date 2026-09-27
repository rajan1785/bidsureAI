import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DB_PATH = Path(os.environ.get("COMPLYGEM_DB", Path(__file__).parents[1] / "app.db"))
UPLOADS_DIR = Path(__file__).parents[1] / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

engine = create_engine(
    f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app import models  # noqa: F401

    Base.metadata.create_all(engine)
    # create_all does not add columns to an existing SQLite database.
    # Add the deadline column in place so existing installations keep working.
    if engine.dialect.name == "sqlite":
        from sqlalchemy import inspect, text

        with engine.begin() as connection:
            columns = {column["name"] for column in inspect(connection).get_columns("tenders")}
            if "deadline" not in columns:
                connection.execute(text("ALTER TABLE tenders ADD COLUMN deadline VARCHAR NOT NULL DEFAULT ''"))
            audit_columns = {column["name"] for column in inspect(connection).get_columns("audit_events")}
            if "organization_id" not in audit_columns:
                connection.execute(text("ALTER TABLE audit_events ADD COLUMN organization_id INTEGER REFERENCES organizations(id)"))
