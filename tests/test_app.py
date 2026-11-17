"""
Automated Test Suite for FreelancePilot.
Tests database models, validators, formatting helpers, invoice service,
PDF generation, backup management, and AI provider routing.
"""

import os
import unittest
from datetime import datetime, timedelta

from database.db import init_db, SessionLocal
from database.models import Client, Project, Task, Invoice, InvoiceItem, Expense, Template
from utils.validators import validate_email, validate_non_empty, validate_amount
from utils.helpers import format_currency, format_date, get_relative_date_string
from services.invoice_service import InvoiceService
from services.pdf_service import PDFService
from services.backup_service import BackupService
from services.ai_service import AIProviderManager


class TestFreelancePilot(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()

    def test_validators(self):
        # Email validator
        ok, _ = validate_email("alex@studio.com")
        self.assertTrue(ok)
        ok, err = validate_email("invalid-email")
        self.assertFalse(ok)
        self.assertIsNotNone(err)

        # Non-empty validator
        ok, _ = validate_non_empty("Title")
        self.assertTrue(ok)
        ok, _ = validate_non_empty("   ")
        self.assertFalse(ok)

        # Amount validator
        ok, val, _ = validate_amount("$1,250.50")
        self.assertTrue(ok)
        self.assertEqual(val, 1250.50)
        ok, _, err = validate_amount("-50")
        self.assertFalse(ok)

    def test_helpers(self):
        self.assertEqual(format_currency(1500.0), "$1,500.00")
        self.assertEqual(format_currency(0.0), "$0.00")
        now = datetime.now()
        self.assertEqual(get_relative_date_string(now), "Today")
        self.assertEqual(get_relative_date_string(now + timedelta(days=1)), "Tomorrow")
        self.assertEqual(get_relative_date_string(now - timedelta(days=1)), "Yesterday")

    def test_database_models(self):
        db = SessionLocal()
        try:
            # Verify seed clients exist
            clients = db.query(Client).all()
            self.assertGreater(len(clients), 0)

            # Verify seed projects
            projects = db.query(Project).all()
            self.assertGreater(len(projects), 0)

            # Verify seed templates
            templates = db.query(Template).all()
            self.assertGreaterEqual(len(templates), 5)
        finally:
            db.close()

    def test_invoice_service(self):
        next_num = InvoiceService.generate_next_invoice_number()
        self.assertTrue(next_num.startswith("INV-"))

        # Verify marking status
        db = SessionLocal()
        inv = db.query(Invoice).first()
        inv_id = inv.id
        db.close()

        InvoiceService.mark_status(inv_id, "Paid")
        db = SessionLocal()
        updated_inv = db.query(Invoice).filter(Invoice.id == inv_id).first()
        self.assertEqual(updated_inv.status, "Paid")
        db.close()

    def test_pdf_service(self):
        db = SessionLocal()
        inv = db.query(Invoice).first()
        pdf_path = PDFService.generate_invoice_pdf(inv)
        db.close()

        self.assertTrue(os.path.exists(pdf_path))
        self.assertGreater(os.path.getsize(pdf_path), 1000)

        # Proposal PDF
        prop_path = PDFService.generate_proposal_pdf(
            proposal_title="Unit Test Proposal",
            client_name="Test Client Corp",
            content="## Overview\nThis is a test proposal."
        )
        self.assertTrue(os.path.exists(prop_path))
        self.assertGreater(os.path.getsize(prop_path), 1000)

    def test_backup_service(self):
        ok, msg = BackupService.create_backup("unittest")
        self.assertTrue(ok)
        backups = BackupService.list_backups()
        self.assertGreater(len(backups), 0)

    def test_keyring_storage(self):
        AIProviderManager.set_api_key("gemini", "secret_gemini_token")
        retrieved = AIProviderManager.get_api_key("gemini")
        self.assertEqual(retrieved, "secret_gemini_token")
        AIProviderManager.set_api_key("gemini", "")


if __name__ == "__main__":
    unittest.main()
