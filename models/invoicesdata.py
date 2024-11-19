from sqlalchemy import (
    Column,
    String,
    Date,
    Integer,
    Boolean,
    Float
)

from models.base import Base

class InvoiceData(Base):
    __tablename__ = "invoice_data"
    
    id = Column(Integer, primary_key=True, index=True)
    Date = Column(Date, index=True)
    InvoiceNumber = Column(String, index=True)
    ClientName = Column(String, index=True)
    Amount = Column(Float, index=True)
    Status = Column(String, index=True)
    
    class Config:
        from_attributes = True

