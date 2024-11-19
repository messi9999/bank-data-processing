from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, Session
from databases import Database

from models.base import Base

from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Accessing the variables
PG_DB_USERNAME = os.getenv('PG_DB_USERNAME')
PG_DB_PASSWORD = os.getenv('PG_DB_PASSWORD')
PG_DB_HOST = os.getenv('PG_DB_HOST')
PG_DB_PORT = os.getenv('PG_DB_PORT')
PG_DB_NAME = os.getenv('PG_DB_NAME')

DATABASE_URL = f"postgresql://{PG_DB_USERNAME}:{PG_DB_PASSWORD}@{PG_DB_HOST}:{PG_DB_PORT}/{PG_DB_NAME}"

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