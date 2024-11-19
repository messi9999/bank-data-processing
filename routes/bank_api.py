from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.bankdata import BankData1
from schemas.bankdata_schemas import BankDataCreateReq
from config.database import get_db_session

import pandas as pd


# Create a new instance of APIRouter
api_router = APIRouter()

# @api_router.post("/bank-data1/")
# def create_bank_data(bank_data: BankDataCreateReq):
#     print(bank_data)
#     return bank_data

def load_excel_data(file_path: str):
    # Load the Excel file, skipping the first three rows
    df = pd.read_excel(file_path, skiprows=3)
    return df



@api_router.post("/bank-data1/")
def create_bank_data(bank_data: BankDataCreateReq, db: Session = Depends(get_db_session)):
    file_names = bank_data["file_names"]
    data = pd.DataFrame()
    for file_name in file_names:
        data = load_excel_data(file_path=f"excels/{file_name}")
        # Filter the DataFrame
        df_filtered = data.loc[data["Nature de l'opération"] == 'Virements reçus']
        df_filtered['Bank'] = 'Banque Principale'
        df_filtered['Date opération'] = pd.to_datetime(df_filtered['Date opération'])
        df_filtered.sort_values(by='Date opération', inplace=True)
        df_filtered['TransactionNumber'] = df_filtered.groupby('Date opération').cumcount() + 1
        df_filtered['TransactionNumber'] = 'C' + df_filtered['Date opération'].dt.strftime('%y%m%d') + df_filtered['TransactionNumber'].apply(lambda x: f'{x:03}')

        
        
        for index, row in df_filtered.iterrows():
            db_bank_data = BankData1(
                bank = "Bank",
                bank_date = row["Date opération"],
                wording = row["Libelle"],
                client_name = row["Libelle"],
                client_number = row["Libelle"],
                transaction_number = row["TransactionNumber"],
                credit = row["Montant de l'opération"],
                matching = ""
            )
            existing_data = db.query(BankData1).filter_by(transaction_number=db_bank_data.transaction_number).first()
            
            if existing_data:
                continue

            db.add(db_bank_data)
            try:
                db.commit()
                db.refresh(db_bank_data)
            except Exception as e:
                db.rollback()
                raise HTTPException(status_code=500, detail=str(e))
    return {"status": "Success"}