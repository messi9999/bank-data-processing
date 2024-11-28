from pydantic import BaseModel
from datetime import date
from typing import List


class InvoiceDataCreateReq(BaseModel):
    list_file_names: List[str]
    status_file_names: List[str]
    
class InvoiceListDataCreateReq(BaseModel):
    status_file_names: List[str]


# Pydantic schema for bank data output (includes ID)
class InvoiceDataCreateRes(BaseModel):
    id: int
    bank_date: date
    wording: str
    client_name: str
    client_number: str
    transaction_number: str
    credit: str
    matching: str

    class Config:
        from_attributes = True