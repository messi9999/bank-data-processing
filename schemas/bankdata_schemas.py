from pydantic import BaseModel
from datetime import date
from typing import List


class BankDataCreateReq(BaseModel):
    file_names: List[str]


# Pydantic schema for bank data output (includes ID)
class BankDataCreateRes(BaseModel):
    id: int
    bank_date: date
    wording: str
    client_name: str
    client_number: str
    transaction_number: str
    credit: str
    matching: str

    class Config:
        orm_mode = True