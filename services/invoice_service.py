"""
Invoice business logic and number generator for FreelancePilot.
"""

from datetime import datetime
from database.db import SessionLocal
from database.models import Invoice, Activity


class InvoiceService:
    @staticmethod
    def generate_next_invoice_number() -> str:
        """
        Generates the next sequential invoice number format: INV-YYYY-XXX (e.g. INV-2026-004).
        """
        db = SessionLocal()
        try:
            current_year = datetime.now().year
            prefix = f"INV-{current_year}-"

            invoices = db.query(Invoice).filter(Invoice.invoice_number.like(f"{prefix}%")).all()
            max_num = 0
            for inv in invoices:
                parts = inv.invoice_number.split("-")
                if len(parts) == 3 and parts[2].isdigit():
                    num = int(parts[2])
                    if num > max_num:
                        max_num = num

            next_num = max_num + 1
            return f"{prefix}{next_num:03d}"
        finally:
            db.close()

    @staticmethod
    def mark_status(invoice_id: int, new_status: str):
        """
        Updates the invoice status and registers an activity event.
        """
        db = SessionLocal()
        try:
            inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
            if inv:
                old_status = inv.status
                inv.status = new_status

                client_name = inv.client.name if inv.client else "Client"
                if new_status == "Paid":
                    act = Activity(
                        title="Payment Received",
                        description=f"Received ${inv.total:,.2f} for {inv.invoice_number} from {client_name}.",
                        icon="fa5s.check-circle",
                        category="invoice"
                    )
                    db.add(act)
                elif new_status == "Sent":
                    act = Activity(
                        title="Invoice Dispatched",
                        description=f"{inv.invoice_number} (${inv.total:,.2f}) marked as sent to {client_name}.",
                        icon="fa5s.paper-plane",
                        category="invoice"
                    )
                    db.add(act)

                db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
