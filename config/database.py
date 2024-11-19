from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from databases import Database
from sqlalchemy.orm import Session

from models.base import Base

DATABASE_URL = ""

database = Database(DATABASE_URL)
metadata = MetaData()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session() -> Session: # type: ignore
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)


def drop_all_tables():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)