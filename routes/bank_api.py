from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from models.bankdata import BankData
from schemas.bankdata_schemas import BankDataCreateReq
from config.database import get_db_session
from utils.utils import load_excel_data
from pathlib import Path
import pandas as pd
import shutil
import uuid
import os

from sqlalchemy.future import select


# Ensure the excels directory exists
EXCELS_DIR = Path("excels")
EXCELS_DIR.mkdir(exist_ok=True)

# Create a new instance of APIRouter
api_router = APIRouter()


@api_router.post("/bank-data1/")
def create_bank1_data(bank_data: BankDataCreateReq, db: Session = Depends(get_db_session)):
    file_names = bank_data.file_names
    df_combined = pd.DataFrame()
    for file_name in file_names:
        data = load_excel_data(file_path=f"excels/{file_name}")
        df_combined = pd.concat([df_combined, data], ignore_index=True)
        # Filter the DataFrame
    df_filtered = df_combined.loc[df_combined["Nature de l'opération"] == 'Virements reçus']
    df_filtered['Bank'] = 'Banque Principale'
    df_filtered['Date opération'] = pd.to_datetime(df_filtered['Date opération'])
    df_filtered.sort_values(by='Date opération', inplace=True)
    df_filtered['TransactionNumber'] = df_filtered.groupby('Date opération').cumcount() + 1
    df_filtered['TransactionNumber'] = 'C' + df_filtered['Date opération'].dt.strftime('%y%m%d') + df_filtered['TransactionNumber'].apply(lambda x: f'{x:03}')

    db_bank_data_list = []
    for index, row in df_filtered.iterrows():
        db_bank_data = BankData(
            Bank = "Bank",
            Date = row["Date opération"],
            Wording = row["Libelle"],
            ClientName = '',
            ClientNumber = "",
            TransactionNumber = row["TransactionNumber"],
            Credit = row["Montant de l'opération"],
            Matching = None
        )
        db_bank_data_list.append(db_bank_data)
    # Add all objects to the session and commit
    
    db.add_all(db_bank_data_list)
    db.commit()
    
    # Optionally refresh to retrieve any generated fields like IDs
    for db_data in db_bank_data_list:
        db.refresh(db_data)
        
    db.execute(text("""
            DELETE FROM bank_data
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM bank_data
                GROUP BY "Bank", "Date", "Wording", "ClientName",
                        "ClientNumber", "Credit"
            );
        """))
    db.commit()



    return {"status": "Success"}



@api_router.post("/bank-data2/")
def create_bank2_data(bank_data: BankDataCreateReq, db: Session = Depends(get_db_session)):
    file_names = bank_data.file_names
    df_combined = pd.DataFrame()
    for file_name in file_names:
        data = load_excel_data(file_path=f"excels/{file_name}")
        df_combined = pd.concat([df_combined, data], ignore_index=True)
        
    # Implement the following logic formulas.  Ignore or keep lines depending on result
    def filter_pairs(group):
        # Find the indices of rows in the group where 'Montant' has a negative counterpart
        indices_to_remove = group[group['Montant'].isin(-group['Montant'])].index
        # Drop these indices from the group
        return group.drop(indices_to_remove)
    data_filtered = df_combined.groupby('Acheteur', group_keys=False).apply(filter_pairs).reset_index(drop=True)
    
    # Remove all lines that doesn’t have « Encaissement de virement » as value in column E « Type réglement ».
    data_filtered = data_filtered.loc[data_filtered['Type réglement'] == 'Encaissement de virement']
    
    db_bank_data_list = []
    for index, row in data_filtered.iterrows():
        db_bank_data = BankData(
            Bank = "Factor",
            Date = row["Date document"],
            Wording = "",
            ClientName = row["Acheteur"],
            ClientNumber = row["Numero compte"],
            TransactionNumber = row["Numéro réglement"],
            Credit = row["Montant"],
            Matching = None
        )
        db_bank_data_list.append(db_bank_data)
    
    db.add_all(db_bank_data_list)
    db.commit()
    
    # Optionally refresh to retrieve any generated fields like IDs
    for db_data in db_bank_data_list:
        db.refresh(db_data)
        
    db.execute(text("""
            DELETE FROM bank_data
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM bank_data
                GROUP BY "Bank", "Date", "Wording", "ClientName",
                        "ClientNumber", "Credit"
            );
        """))
    db.commit()

            
    return {"status": "Success"}


@api_router.post("/bank-data1-process/")
async def bank_data1_process(files: list[UploadFile] = File(...), db: Session = Depends(get_db_session)):
    file_names = []
    file_locations = []
    for file in files:
        # Generate a unique file name
        unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
        try:
            file_location = EXCELS_DIR / unique_filename
            with file_location.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
                file_locations.append(file_location)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Could not save file: {e}")
        finally:
            await file.close()
        
        file_names.append(unique_filename)
        

    df_combined = pd.DataFrame()
    for file_name in file_names:
        data = load_excel_data(file_path=f"excels/{file_name}", skiprows=3)
        df_combined = pd.concat([df_combined, data], ignore_index=True)
        # Filter the DataFrame
    df_filtered = df_combined.loc[df_combined["Nature de l'opération"] == 'Virements reçus']
    df_filtered['Bank'] = 'Banque Principale'
    df_filtered['Date opération'] = pd.to_datetime(df_filtered['Date opération'])
    df_filtered.sort_values(by='Date opération', inplace=True)
    df_filtered['TransactionNumber'] = df_filtered.groupby('Date opération').cumcount() + 1
    df_filtered['TransactionNumber'] = 'C' + df_filtered['Date opération'].dt.strftime('%y%m%d') + df_filtered['TransactionNumber'].apply(lambda x: f'{x:03}')

    for f in file_locations:
        try:
            os.remove(f)
        except OSError as e:
            print(f"Error: {f} : {e.strerror}")
    
    db_bank_data_list = []
    for index, row in df_filtered.iterrows():
        db_bank_data = BankData(
            Bank = "Banque Principale",
            Date = row["Date opération"],
            Wording = row["Libelle"],
            ClientName = '',
            ClientNumber = "",
            TransactionNumber = row["TransactionNumber"],
            Credit = row["Montant de l'opération"],
            Matching = None
        )
        db_bank_data_list.append(db_bank_data)
    # Add all objects to the session and commit
    
    db.add_all(db_bank_data_list)
    db.commit()
    
    # Optionally refresh to retrieve any generated fields like IDs
    for db_data in db_bank_data_list:
        db.refresh(db_data)
        
    db.execute(text("""
            DELETE FROM bank_data
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM bank_data
                GROUP BY "Bank", "Date", "Wording", "ClientName",
                        "ClientNumber", "Credit"
            );
        """))
    db.commit()
    
    
    
    
    return {"status": "Success"}


@api_router.post("/bank-data2-process/")
async def bank_data2_process(files: list[UploadFile] = File(...), db: Session = Depends(get_db_session)):
    file_names = []
    file_locations = []
    for file in files:
        # Generate a unique file name
        unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
        try:
            file_location = EXCELS_DIR / unique_filename
            with file_location.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
                file_locations.append(file_location)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Could not save file: {e}")
        finally:
            await file.close()
        
        file_names.append(unique_filename)
        
    df_combined = pd.DataFrame()
    for file_name in file_names:
        data = load_excel_data(file_path=f"excels/{file_name}")
        df_combined = pd.concat([df_combined, data], ignore_index=True)
        
    # Implement the following logic formulas.  Ignore or keep lines depending on result
    def filter_pairs(group):
        # Find the indices of rows in the group where 'Montant' has a negative counterpart
        indices_to_remove = group[group['Montant'].isin(-group['Montant'])].index
        # Drop these indices from the group
        return group.drop(indices_to_remove)
    data_filtered = df_combined.groupby('Acheteur', group_keys=False).apply(filter_pairs).reset_index(drop=True)
    
    # Remove all lines that doesn’t have « Encaissement de virement » as value in column E « Type réglement ».
    data_filtered = data_filtered.loc[data_filtered['Type réglement'] == 'Encaissement de virement']
    
    db_bank_data_list = []
    for index, row in data_filtered.iterrows():
        db_bank_data = BankData(
            Bank = "Factor",
            Date = row["Date document"],
            Wording = "",
            ClientName = row["Acheteur"],
            ClientNumber = row["Numero compte"],
            TransactionNumber = row["Numéro réglement"],
            Credit = row["Montant"],
            Matching = None
        )
        db_bank_data_list.append(db_bank_data)
    
    db.add_all(db_bank_data_list)
    db.commit()
    
    # Optionally refresh to retrieve any generated fields like IDs
    for db_data in db_bank_data_list:
        db.refresh(db_data)
        
    db.execute(text("""
            DELETE FROM bank_data
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM bank_data
                GROUP BY "Bank", "Date", "Wording", "ClientName",
                        "ClientNumber", "Credit"
            );
        """))
    db.commit()
    
    for f in file_locations:
        try:
            os.remove(f)
        except OSError as e:
            print(f"Error: {f} : {e.strerror}")

            
    return {"status": "Success"}
    