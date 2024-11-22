from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from config.database import get_db_session
import pandas as pd

from datetime import datetime
import os


# Create a new instance of APIRouter
api_router = APIRouter()

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
                invoice_numbers = ', '.join([str(inv.InvoiceNumber) for inv in matching_invoices])
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
        
        
        query2 = text("""
        SELECT "Bank", "Date", "Wording", "Credit", "TransactionNumber"
        FROM bank_data
        WHERE "Matching" IS NULL OR "Matching" = ''
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

        # Step 5: Optionally, return a response
        return {
            "message": "File saved successfully", 
            "export1": f"{os.getenv('BASE_URL')}/{file_path1}", 
            "export2": f"{os.getenv('BASE_URL')}/{file_path2}"
        }