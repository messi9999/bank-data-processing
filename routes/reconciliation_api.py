from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import text
from sqlalchemy.orm import Session
from config.database import get_db_session
import pandas as pd
from pathlib import Path
import shutil
import uuid

from utils.utils import load_excel_data, load_excel_sheet

from datetime import datetime
import os
import zipfile


# Create a new instance of APIRouter
api_router = APIRouter()


# Ensure the excels directory exists
EXCELS_DIR = Path("excels")
EXCELS_DIR.mkdir(exist_ok=True)

def find_invoices_subset(invoices, bank_amount, partial=[]):
    s = sum(invoice.Amount for invoice in partial)

    # Check if the partial sum is equals to target
    if s == bank_amount:
        return partial
    if s >= bank_amount:
        return None

    for i in range(len(invoices)):
        n = invoices[i]
        remaining = invoices[i+1:]
        subset = find_invoices_subset(remaining, bank_amount, partial + [n])
        if subset:
            return subset

    return None

@api_router.get("/reconciliation/")
def create_invoice_list(db: Session = Depends(get_db_session)):
        # Step 1: Fetch all eligible bank_data and invoice_data
        bank_data_query = text("""
            SELECT id, "Credit", "TransactionNumber"
            FROM bank_data
        """)
        bank_data_entries = db.execute(bank_data_query).fetchall()

        invoice_data_query = text("""
            SELECT id, "Amount", "Status", "InvoiceNumber"
            FROM invoice_data
            WHERE "Status" NOT IN ('Soldée')
        """)
        invoice_data_entries = db.execute(invoice_data_query).fetchall()
        
        filtered_invoices = []
        
        for invoice in invoice_data_entries:
            if invoice.Status is not "Soldée" and invoice.Status is not "soldée":
                filtered_invoices.append(invoice)
        
        print(filtered_invoices)

        # Step 2: Match credits with invoices
        for bank_entry in bank_data_entries:
            bank_id = bank_entry.id
            credit = bank_entry.Credit
            transaction_number = bank_entry.TransactionNumber

            # matching_invoices = [
            #     invoice for invoice in invoice_data_entries
            #     if invoice.Amount == credit and invoice.Status not in ('Soldée', transaction_number)
            # ]
            
            matching_invoices = find_invoices_subset(filtered_invoices, credit)
            print("credit: ", credit)
            print("machings: ", matching_invoices)
            
                

            if matching_invoices:
                # Update the Matching field in bank_data
                # invoice_numbers = ', '.join([str(inv.InvoiceNumber) for inv in matching_invoices])
                invoice_numbers = [str(inv.InvoiceNumber) for inv in matching_invoices]
                invoice_amounts = [str(inv.Amount) for inv in matching_invoices]
                update_bank_data_query = text("""
                    UPDATE bank_data
                    SET "Matching" = :invoice_numbers
                    WHERE id = :bank_id
                """)
                db.execute(update_bank_data_query, {"invoice_numbers": invoice_numbers, "bank_id": bank_id})

                # Update the Status field in invoice_data
                for invoice in matching_invoices:
                    update_invoice_data_query = text("""
                        UPDATE invoice_data
                        SET "Status" = :transaction_number
                        WHERE id = :invoice_id
                    """)
                    db.execute(update_invoice_data_query, {"transaction_number": transaction_number, "invoice_id": invoice.id})

                filtered_invoices = [f_invoice for f_invoice in filtered_invoices if f_invoice.Amount not in invoice_amounts]
        # Commit the changes
        db.commit()

        # Step 3: Return updated bank_data
        updated_bank_data_query = text("""
            SELECT * FROM bank_data
        """)
        updated_bank_data = db.execute(updated_bank_data_query).fetchall()
        data1 = {
            "Date d'encaissement": [row.Date for row in updated_bank_data],
            "Montant perçu": [row.Credit for row in updated_bank_data],
            "Mode de paiement": ["Virement"] * len(updated_bank_data),  # Assuming 'Virement' is constant
            "N° du Règlement": [row.TransactionNumber for row in updated_bank_data],
            "Compte bancaire": [row.Bank for row in updated_bank_data],
            "Commentaire": ["" for _ in updated_bank_data],  # Assuming no data available
            "Lettrage": [row.Matching for row in updated_bank_data]
        }
        df1 = pd.DataFrame(data1)
        static_folder = 'exports/'  # Adjust the path as needed
        date_str = datetime.now().strftime("%y%m%d")
        serial_number = "001"  # Replace with logic to generate a serial number if needed
        filename1 = f"Encaissements à enregistrer dans Cinego {date_str}{serial_number}.xlsx"
        file_path1 = os.path.join(static_folder, filename1)
        
        # Step 4: Save the Excel file
        with pd.ExcelWriter(file_path1, engine='xlsxwriter') as writer:
            df1.to_excel(writer, index=False, sheet_name='BankData')
            # Get the xlsxwriter workbook and worksheet objects.
            workbook  = writer.book
            worksheet = writer.sheets['BankData']
            
            # Set the column widths
            worksheet.set_column('A:A', 17.5)  # Set the width of column A to 20
            worksheet.set_column('B:B', 12.5)  # Set the width of column B to 15
            worksheet.set_column('C:C', 15.83)  # Set the width of column C to 25
            worksheet.set_column('D:D', 14.7)  # Set the width of column C to 25
            worksheet.set_column('E:E', 14.7)  # Set the width of column C to 25
            worksheet.set_column('F:F', 10.83)  # Set the width of column C to 25
            worksheet.set_column('G:G', 30.83)  # Set the width of column C to 25
        
        
        query2 = text("""
        SELECT "Bank", "Date", "Wording", "Credit", "TransactionNumber"
        FROM bank_data
        WHERE "Matching" IS NULL
        """)
        non_matched_entries = db.execute(query2).fetchall()
        data2 = {
            "Compte bancaire": [row.Bank for row in non_matched_entries],
            "Date d'encaissement ": [row.Date for row in non_matched_entries],
            "Libelle": [row.Wording for row in non_matched_entries],
            "Montant perçu": [row.Credit for row in non_matched_entries],
            "N° du Règlement": [row.TransactionNumber for row in non_matched_entries]
        }
        df2 = pd.DataFrame(data2)

        # Step 2: Create a CSV file
        filename2 = f"Lettrage non effectué {date_str}{serial_number}.xlsx"
        file_path2 = os.path.join(static_folder, filename2)
        
        with pd.ExcelWriter(file_path2, engine='xlsxwriter') as writer:
            df2.to_excel(writer, index=False, sheet_name='BankData')
            # Get the xlsxwriter workbook and worksheet objects.
            workbook  = writer.book
            worksheet = writer.sheets['BankData']
            
            # Set the column widths
            worksheet.set_column('A:A', 14.7)  # Set the width of column A to 20
            worksheet.set_column('B:B', 17.5)  # Set the width of column B to 15
            worksheet.set_column('C:C', 17.5)  # Set the width of column C to 25
            worksheet.set_column('D:D', 12.5)  # Set the width of column C to 25
            worksheet.set_column('E:E', 14.7)  # Set the width of column C to 25
        
        # Define the name of the resulting zip file
        unique_filename = f"{uuid.uuid4().hex}_result.zip"
        zip_filename = os.path.join(static_folder, unique_filename)

        # Create a zip file and add the two files
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            zipf.write(file_path1, os.path.basename(file_path1))
            zipf.write(file_path2, os.path.basename(file_path2))


        # Step 5: Optionally, return a response
        return {
            "message": "File saved successfully", 
            "export": f"{os.getenv('BASE_URL')}/{zip_filename}"
        }


@api_router.post("/pre-reconciliation/")
async def pre_reconciliation(files: list[UploadFile] = File(...), db: Session = Depends(get_db_session)):
    file_names = []
    for file in files:
        # Generate a unique file name
        unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
        file_locations = []
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
        data = load_excel_sheet(file_path=f"excels/{file_name}")
        df_combined = pd.concat([df_combined, data], ignore_index=True)
    for f in file_locations:
        try:
            os.remove(f)
        except OSError as e:
            print(f"Error: {f} : {e.strerror}")
    # transaction_sums = data.groupby('Numéro')['Montant TTC'].sum()
    transaction_aggregates = df_combined.groupby('Numéro').agg({
        'Montant TTC': 'sum',
        'Facture': lambda x: list(x)
    })
    
    # Step 1: Fetch all eligible bank_data and invoice_data
    bank_data_query = text("""
        SELECT id, "Credit", "TransactionNumber"
        FROM bank_data
    """)
    bank_data_entries = db.execute(bank_data_query).fetchall()
    
    # Step 2: Match credits with invoices
    for bank_entry in bank_data_entries:
        bank_id = bank_entry.id
        credit = bank_entry.Credit
        transaction_number = bank_entry.TransactionNumber
        
        for index, row in transaction_aggregates.iterrows():
            if str(credit) == str(row["Montant TTC"]):
                invoice_numbers = row['Facture']
                update_bank_data_query = text("""
                    UPDATE bank_data
                    SET "Matching" = :invoice_numbers
                    WHERE id = :bank_id
                """)
                db.execute(update_bank_data_query, {"invoice_numbers": invoice_numbers, "bank_id": bank_id})
                

    # Commit the changes
    db.commit() 
    
    
    return {"status": "Success"}
            
        
    