from sqlalchemy import (
    Column,
    String,
    Date,
    Integer,
    Boolean,
    Float
)

from .base import Base

class InvoiceData(Base):
    __tablename__ = "invoice_data"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_date = Column(Date, index=True)
    wording = Column(String, index=True)
    client_name = Column(String, index=True)
    Amount = Column(Float, index=True)
    Status = Column(Boolean, index=True)
    
    
    