from sqlalchemy import (
    Column,
    String,
    Date,
    Integer,
    Float,
    Text
)

from models.base import Base

class BankData(Base):
    __tablename__ = "bank_data"
    
    id = Column(Integer, primary_key=True, index=True)
    Bank = Column(String, index=True)
    Date = Column(Date, index=True)
    Wording = Column(String, index=True)
    ClientName = Column(String, index=True)
    ClientNumber = Column(String, index=True)
    TransactionNumber = Column(String, index=True)
    Credit = Column(Float, index=True)
    Matching = Column(Text, index=True)
    
    class Config:
        from_attributes = True
    