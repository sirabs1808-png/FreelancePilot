"""
Invoices View for FreelancePilot.
Supports creating, editing, PDF exporting, and payment tracking for invoices.
"""

from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QComboBox, QFrame,
    QMessageBox, QDialog, QFileDialog
)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QFont, QDesktopServices
import qtawesome as qta

from database.db import SessionLocal
from database.models import Invoice, Client
from components.dialogs import InvoiceDialog, InvoiceDetailDialog
from components.cards import StatCard, StatusBadge
from services.pdf_service import PDFService
from services.invoice_service import InvoiceService
from utils.helpers import format_currency, format_date


class InvoicesView(QWidget):
    """
    Invoice Management and Billing Screen.
    """
    data_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.invoices = []
        self.init_ui()
        self.load_invoices()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 32)
        layout.setSpacing(20)

        # 1. Header Banner
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Invoices & Billing")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #F8FAFC;")
        sub = QLabel("Generate client invoices, export print-ready PDFs, and track payment receipts.")
        sub.setFont(QFont("Segoe UI", 10))
        sub.setStyleSheet("color: #94A3B8;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        header.addStretch()

        self.create_btn = QPushButton(" + Create Invoice")
        self.create_btn.setObjectName("primaryButton")
        self.create_btn.setCursor(Qt.PointingHandCursor)
        self.create_btn.clicked.connect(self.open_create_dialog)
        header.addWidget(self.create_btn)
        layout.addLayout(header)

        # 2. Stats Strip
        self.stats_row = QHBoxLayout()
        self.stats_row.setSpacing(14)

        self.stat_total = StatCard("TOTAL BILLED", "$0.00", "fa5s.file-invoice-dollar", "Gross invoice volume", True, "#3B82F6")
        self.stat_paid = StatCard("COLLECTED REVENUE", "$0.00", "fa5s.check-double", "Paid into account", True, "#10B981")
        self.stat_pending = StatCard("OUTSTANDING", "$0.00", "fa5s.hourglass-half", "Awaiting collection", False, "#F59E0B")

        self.stats_row.addWidget(self.stat_total)
        self.stats_row.addWidget(self.stat_paid)
        self.stats_row.addWidget(self.stat_pending)
        layout.addLayout(self.stats_row)

        # 3. Filter & Search Bar
        action_bar = QHBoxLayout()
        action_bar.setSpacing(12)

        search_frame = QFrame()
        search_frame.setStyleSheet("""
            QFrame {
                background-color: #181B22;
                border: 1px solid #282E3A;
                border-radius: 8px;
            }
        """)
        s_layout = QHBoxLayout(search_frame)
        s_layout.setContentsMargins(10, 4, 10, 4)
        s_layout.setSpacing(8)

        s_icon = QLabel()
        s_icon.setPixmap(qta.icon("fa5s.search", color="#64748B").pixmap(14, 14))
        s_icon.setStyleSheet("border: none; background: transparent;")
        s_layout.addWidget(s_icon)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by invoice # or client name...")
        self.search_box.setStyleSheet("background: transparent; border: none; color: #F8FAFC;")
        self.search_box.textChanged.connect(self.filter_invoices)
        s_layout.addWidget(self.search_box)
        action_bar.addWidget(search_frame, 1)

        # Status filter dropdown
        status_lbl = QLabel("Status:")
        status_lbl.setStyleSheet("color: #94A3B8; font-weight: 500;")
        action_bar.addWidget(status_lbl)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Invoices", "Paid", "Sent", "Draft", "Overdue", "Cancelled"])
        self.status_filter.setFixedWidth(140)
        self.status_filter.currentTextChanged.connect(lambda _: self.filter_invoices())
        action_bar.addWidget(self.status_filter)

        refresh_btn = QPushButton(" Refresh")
        refresh_btn.setIcon(qta.icon("fa5s.sync", color="#94A3B8"))
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.load_invoices)
        action_bar.addWidget(refresh_btn)

        layout.addLayout(action_bar)

        # 4. Invoices Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Invoice #", "Client", "Issue Date", "Due Date", "Total", "Status", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.cellDoubleClicked.connect(self.on_row_double_click)
        layout.addWidget(self.table, 1)

    def load_invoices(self):
        db = SessionLocal()
        try:
            self.invoices = db.query(Invoice).order_by(Invoice.issue_date.desc()).all()
            self.display_invoices(self.invoices)

            # Update stats
            total_sum = sum(inv.total for inv in self.invoices)
            paid_sum = sum(inv.total for inv in self.invoices if inv.status == "Paid")
            pending_sum = sum(inv.total for inv in self.invoices if inv.status in ["Sent", "Draft", "Overdue"])

            self.stat_total.update_value(format_currency(total_sum))
            self.stat_paid.update_value(format_currency(paid_sum))
            self.stat_pending.update_value(format_currency(pending_sum))
        finally:
            db.close()

    def display_invoices(self, invoices):
        self.table.setRowCount(len(invoices))
        for row, inv in enumerate(invoices):
            # Invoice #
            self.table.setItem(row, 0, QTableWidgetItem(inv.invoice_number))

            # Client
            client_name = inv.client.company or inv.client.name if inv.client else "—"
            self.table.setItem(row, 1, QTableWidgetItem(client_name))

            # Dates
            self.table.setItem(row, 2, QTableWidgetItem(format_date(inv.issue_date)))
            self.table.setItem(row, 3, QTableWidgetItem(format_date(inv.due_date)))

            # Total
            sym = "$" if inv.currency == "USD" else ("€" if inv.currency == "EUR" else "£")
            self.table.setItem(row, 4, QTableWidgetItem(format_currency(inv.total, symbol=sym)))

            # Status Badge widget
            status_container = QWidget()
            s_layout = QHBoxLayout(status_container)
            s_layout.setContentsMargins(4, 2, 4, 2)
            s_layout.setAlignment(Qt.AlignCenter)
            badge = StatusBadge(inv.status)
            s_layout.addWidget(badge)
            self.table.setCellWidget(row, 5, status_container)

            # Actions widget
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(6, 2, 6, 2)
            actions_layout.setSpacing(6)

            view_btn = QPushButton()
            view_btn.setIcon(qta.icon("fa5s.eye", color="#38BDF8"))
            view_btn.setToolTip("View Invoice Details")
            view_btn.setFixedSize(28, 28)
            view_btn.setCursor(Qt.PointingHandCursor)
            view_btn.clicked.connect(lambda _, iid=inv.id: self.open_detail_dialog(iid))
            actions_layout.addWidget(view_btn)

            pdf_btn = QPushButton()
            pdf_btn.setIcon(qta.icon("fa5s.file-pdf", color="#EF4444"))
            pdf_btn.setToolTip("Export PDF")
            pdf_btn.setFixedSize(28, 28)
            pdf_btn.setCursor(Qt.PointingHandCursor)
            pdf_btn.clicked.connect(lambda _, invoice_obj=inv: self.export_pdf(invoice_obj))
            actions_layout.addWidget(pdf_btn)

            if inv.status != "Paid":
                pay_btn = QPushButton()
                pay_btn.setIcon(qta.icon("fa5s.check", color="#10B981"))
                pay_btn.setToolTip("Mark as Paid")
                pay_btn.setFixedSize(28, 28)
                pay_btn.setCursor(Qt.PointingHandCursor)
                pay_btn.clicked.connect(lambda _, iid=inv.id: self.mark_as_paid(iid))
                actions_layout.addWidget(pay_btn)

            edit_btn = QPushButton()
            edit_btn.setIcon(qta.icon("fa5s.edit", color="#F59E0B"))
            edit_btn.setToolTip("Edit Invoice")
            edit_btn.setFixedSize(28, 28)
            edit_btn.setCursor(Qt.PointingHandCursor)
            edit_btn.clicked.connect(lambda _, invoice_obj=inv: self.open_edit_dialog(invoice_obj))
            actions_layout.addWidget(edit_btn)

            del_btn = QPushButton()
            del_btn.setIcon(qta.icon("fa5s.trash-alt", color="#EF4444"))
            del_btn.setToolTip("Delete Invoice")
            del_btn.setFixedSize(28, 28)
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.clicked.connect(lambda _, iid=inv.id, inum=inv.invoice_number: self.delete_invoice(iid, inum))
            actions_layout.addWidget(del_btn)

            self.table.setCellWidget(row, 6, actions_widget)

    def filter_invoices(self):
        query = self.search_box.text().lower().strip()
        status_filter = self.status_filter.currentText()

        filtered = self.invoices
        if status_filter != "All Invoices":
            filtered = [inv for inv in filtered if inv.status == status_filter]

        if query:
            filtered = [
                inv for inv in filtered
                if query in inv.invoice_number.lower() or
                (inv.client and (query in inv.client.name.lower() or query in (inv.client.company or "").lower()))
            ]

        self.display_invoices(filtered)

    def open_create_dialog(self):
        diag = InvoiceDialog(parent=self)
        if diag.exec() == QDialog.Accepted:
            self.load_invoices()
            self.data_changed.emit()

    def open_edit_dialog(self, invoice: Invoice):
        diag = InvoiceDialog(invoice=invoice, parent=self)
        if diag.exec() == QDialog.Accepted:
            self.load_invoices()
            self.data_changed.emit()

    def open_detail_dialog(self, invoice_id: int):
        diag = InvoiceDetailDialog(invoice_id=invoice_id, parent=self)
        if diag.exec() == QDialog.Accepted:
            self.load_invoices()
            self.data_changed.emit()

    def on_row_double_click(self, row, col):
        if row < len(self.invoices):
            self.open_detail_dialog(self.invoices[row].id)

    def mark_as_paid(self, invoice_id: int):
        try:
            InvoiceService.mark_status(invoice_id, "Paid")
            self.load_invoices()
            self.data_changed.emit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to mark invoice as paid: {e}")

    def export_pdf(self, invoice: Invoice):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save PDF Invoice",
            f"{invoice.invoice_number}.pdf",
            "PDF Files (*.pdf)"
        )
        if file_path:
            try:
                PDFService.generate_invoice_pdf(invoice, file_path)
                reply = QMessageBox.question(
                    self,
                    "PDF Generated",
                    f"Invoice successfully saved to:\n{file_path}\n\nWould you like to open it now?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                if reply == QMessageBox.Yes:
                    QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
            except Exception as e:
                QMessageBox.critical(self, "PDF Export Error", f"Failed to generate PDF: {e}")

    def delete_invoice(self, invoice_id: int, invoice_number: str):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete invoice '{invoice_number}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            db = SessionLocal()
            try:
                inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
                if inv:
                    db.delete(inv)
                    db.commit()
                    self.load_invoices()
                    self.data_changed.emit()
            except Exception as e:
                db.rollback()
                QMessageBox.critical(self, "Error", f"Failed to delete invoice: {e}")
            finally:
                db.close()
