from typing import Annotated

from fastapi import Depends
from sqlmodel import create_engine, SQLModel, Session

from ..core import config

sqlite_url = f"sqlite:///{config.SQLITE_FILE_NAME}"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
