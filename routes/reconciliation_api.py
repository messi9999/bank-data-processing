from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from models.bankdata import BankData
from schemas.bankdata_schemas import BankDataCreateReq
from config.database import get_db_session
from utils.utils import load_excel_data
import pandas as pd

from sqlalchemy.future import select


# Create a new instance of APIRouter
api_router = APIRouter()


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

        # Step 2: Match credits with invoices
        for bank_entry in bank_data_entries:
            bank_id = bank_entry.id
            credit = bank_entry.Credit
            transaction_number = bank_entry.TransactionNumber

            matching_invoices = [
                invoice for invoice in invoice_data_entries
                if invoice.Amount == credit and invoice.Status not in ('Soldée', transaction_number)
            ]

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
        result = [dict(row._mapping) for row in updated_bank_data]
        return {"result": result}