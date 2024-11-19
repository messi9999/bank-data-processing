from sqlalchemy import (
    Column,
    String,
    Date,
    Integer,
    Float
)

from .base import Base

class BankData1(Base):
    __tablename__ = "bank_data"
    
    id = Column(Integer, primary_key=True, index=True)
    bank = Column(String, index=True)
    bank_date = Column(Date, index=True)
    wording = Column(String, index=True)
    client_name = Column(String, index=True)
    client_number = Column(String, index=True)
    transaction_number = Column(String, index=True)
    credit = Column(Float, index=True)
    matching = Column(String, index=True)
    
    
    