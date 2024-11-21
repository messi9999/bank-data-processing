from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from models.bankdata import BankData
from schemas.bankdata_schemas import BankDataCreateReq
from config.database import get_db_session
from utils.utils import load_excel_data
import pandas as pd

from config import database

from sqlalchemy.future import select


# Create a new instance of APIRouter
api_router = APIRouter()


@api_router.get("/clean_all_records/")
def clean_all_records(db: Session = Depends(get_db_session)):
    database.drop_all_tables()
    database.create_tables()
    return {"status": "Success"}

