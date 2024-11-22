from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from models.invoicesdata import InvoiceData
from config.database import get_db_session
from utils.utils import load_excel_data_without_header, load_excel_data
import pandas as pd

from schemas.invoice_schemas import InvoiceDataCreateReq



# Create a new instance of APIRouter
api_router = APIRouter()

@api_router.post("/invoice-list/")
def create_invoice_list(invoice_data: InvoiceDataCreateReq, db: Session = Depends(get_db_session)):
    list_file_names = invoice_data.list_file_names
    status_file_names = invoice_data.status_file_names
    df_combined_list = pd.DataFrame()
    df_combined_status = pd.DataFrame()
    
    # Process invoice list data
    for list_file_name in list_file_names:
        data = load_excel_data_without_header(file_path=f"excels/{list_file_name}")
        df_combined_list = pd.concat([df_combined_list, data], ignore_index=True)
    # Get the number of columns in the DataFrame
    num_columns = data.shape[1]

    # Generate column names based on the number of columns
    column_names = [f'Column{i+1}' for i in range(num_columns)]

    # Assign the generated column names to the DataFrame
    data.columns = column_names
    # Filter the DataFrame
    
    df_filtered = data.dropna(subset=['Column6'])
    df_filtered = df_filtered[df_filtered['Column6'] != 0]
    
    df_filtered['Column7'] = "" 
        
    # Process invoice status data
    for status_file_name in status_file_names:
        data = load_excel_data(file_path=f"excels/{status_file_name}")
        df_combined_status = pd.concat([df_combined_status, data], ignore_index=True)
    
    for invoice_number in df_combined_status['Numéro']:
        # Find the corresponding row in df_filtered and set 'Column7' to 'Soldée'
        df_filtered.loc[df_filtered['Column3'] == invoice_number, 'Column7'] = 'Soldée'
    
    db_invoice_data_list = []
    for index, row in df_filtered.iterrows():
        formatted_date = pd.to_datetime(row["Column2"], format='%d/%m/%y').strftime('%Y-%m-%d')
        db_invoice_data = InvoiceData(
            Date = formatted_date,
            InvoiceNumber = row["Column3"],
            ClientName = row["Column5"],
            Amount = row["Column6"],
            Status = row["Column7"],
        )
        
        db_invoice_data_list.append(db_invoice_data)
    
    # Add all objects to the session and commit
    
    db.add_all(db_invoice_data_list)
    db.commit()
    
    # Optionally refresh to retrieve any generated fields like IDs
    for db_data in db_invoice_data_list:
        db.refresh(db_data)
        
    db.execute(text("""
            DELETE FROM invoice_data
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM invoice_data
                GROUP BY "Date", "InvoiceNumber", "ClientName",
                        "Amount", "Status"
            );
        """))
    db.commit()
        
        
    return {"status": "Success"}

