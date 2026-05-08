from typing import Annotated

from fastapi import Depends
from sqlalchemy import event
from sqlmodel import create_engine, SQLModel, Session

from ..core import config

sqlite_url = f"sqlite:///{config.SQLITE_FILE_NAME}"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

if engine.dialect.name == "sqlite":
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
