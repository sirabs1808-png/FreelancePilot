"""
Modal Dialog Components for FreelancePilot.
Provides forms for Clients, Projects, Tasks, Invoices, Expenses, and inspector dialogs.
"""

import os
from datetime import datetime, date
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QComboBox, QDateEdit, QSlider, QCheckBox,
    QFrame, QMessageBox, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog
)
from PySide6.QtCore import Qt, QDate, QUrl
from PySide6.QtGui import QFont, QDesktopServices
import qtawesome as qta

from database.db import SessionLocal
from database.models import Client, Project, Task, Invoice, InvoiceItem, Expense, Activity
from utils.validators import validate_email, validate_non_empty, validate_amount
from utils.helpers import format_currency, format_date
from components.cards import StatusBadge
from services.pdf_service import PDFService
from services.invoice_service import InvoiceService


class BaseModalDialog(QDialog):
    """
    Styled base dialog matching FreelancePilot's graphite & electric blue identity.
    """
    def __init__(self, title_text: str, subtitle_text: str = "", parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle(title_text)
        self.setStyleSheet("""
            QDialog {
                background-color: #16191E;
                border: 1px solid #282E3A;
                border-radius: 12px;
            }
            QLabel {
                color: #F8FAFC;
                font-size: 13px;
            }
        """)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 20, 24, 20)
        self.main_layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        header_col = QVBoxLayout()
        header_col.setSpacing(2)

        title_lbl = QLabel(title_text)
        title_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        header_col.addWidget(title_lbl)

        if subtitle_text:
            sub_lbl = QLabel(subtitle_text)
            sub_lbl.setFont(QFont("Segoe UI", 9))
            sub_lbl.setStyleSheet("color: #94A3B8;")
            header_col.addWidget(sub_lbl)

        header_layout.addLayout(header_col)
        header_layout.addStretch()

        close_btn = QPushButton()
        close_btn.setFixedSize(28, 28)
        close_btn.setIcon(qta.icon("fa5s.times", color="#94A3B8"))
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #282E3A;
            }
        """)
        close_btn.clicked.connect(self.reject)
        header_layout.addWidget(close_btn)
        self.main_layout.addLayout(header_layout)

        # Error Banner (Hidden by default)
        self.error_banner = QLabel()
        self.error_banner.setWordWrap(True)
        self.error_banner.setStyleSheet("""
            background-color: #EF444422;
            color: #FCA5A5;
            border: 1px solid #EF444455;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 12px;
        """)
        self.error_banner.hide()
        self.main_layout.addWidget(self.error_banner)

        # Form content body
        self.body_layout = QVBoxLayout()
        self.body_layout.setSpacing(12)
        self.main_layout.addLayout(self.body_layout)

        # Bottom Action Bar
        self.actions_layout = QHBoxLayout()
        self.actions_layout.setSpacing(10)
        self.actions_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.reject)
        self.actions_layout.addWidget(self.cancel_btn)

        self.submit_btn = QPushButton("Save")
        self.submit_btn.setObjectName("primaryButton")
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.actions_layout.addWidget(self.submit_btn)

        self.main_layout.addLayout(self.actions_layout)

    def show_error(self, message: str):
        self.error_banner.setText(message)
        self.error_banner.show()

    def hide_error(self):
        self.error_banner.hide()


# ============================================================================
# CLIENT DIALOG
# ============================================================================
class ClientDialog(BaseModalDialog):
    """
    Form dialog to create or edit a client.
    """
    def __init__(self, client: Client = None, parent=None):
        title = "Edit Client" if client else "Add New Client"
        subtitle = "Update client directory record" if client else "Register a new client or organization"
        super().__init__(title, subtitle, parent)
        self.client = client
        self.resize(500, 560)

        self.init_form()
        if client:
            self.load_client_data()

        self.submit_btn.clicked.connect(self.save)

    def init_form(self):
        self.body_layout.addWidget(QLabel("Client Name *"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Marcus Thorne")
        self.body_layout.addWidget(self.name_input)

        self.body_layout.addWidget(QLabel("Company / Organization"))
        self.company_input = QLineEdit()
        self.company_input.setPlaceholderText("e.g. Aura Brand Studio")
        self.body_layout.addWidget(self.company_input)

        self.body_layout.addWidget(QLabel("Email Address *"))
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("e.g. marcus@aurastudio.co")
        self.body_layout.addWidget(self.email_input)

        self.body_layout.addWidget(QLabel("Phone Number"))
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("e.g. +1 (555) 019-2834")
        self.body_layout.addWidget(self.phone_input)

        self.body_layout.addWidget(QLabel("Billing Address"))
        self.address_input = QTextEdit()
        self.address_input.setPlaceholderText("Street, Suite, City, State, ZIP, Country...")
        self.address_input.setFixedHeight(65)
        self.body_layout.addWidget(self.address_input)

        self.body_layout.addWidget(QLabel("Notes & Preferences"))
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Communication habits, timezone, milestone preferences...")
        self.notes_input.setFixedHeight(65)
        self.body_layout.addWidget(self.notes_input)

    def load_client_data(self):
        self.name_input.setText(self.client.name)
        self.company_input.setText(self.client.company or "")
        self.email_input.setText(self.client.email)
        self.phone_input.setText(self.client.phone or "")
        self.address_input.setPlainText(self.client.address or "")
        self.notes_input.setPlainText(self.client.notes or "")

    def save(self):
        self.hide_error()
        name = self.name_input.text().strip()
        email = self.email_input.text().strip()

        ok, err = validate_non_empty(name, "Client Name")
        if not ok:
            self.show_error(err)
            return

        ok, err = validate_email(email)
        if not ok:
            self.show_error(err)
            return

        db = SessionLocal()
        try:
            if self.client:
                c = db.query(Client).filter(Client.id == self.client.id).first()
                if c:
                    c.name = name
                    c.company = self.company_input.text().strip() or None
                    c.email = email
                    c.phone = self.phone_input.text().strip() or None
                    c.address = self.address_input.toPlainText().strip() or None
                    c.notes = self.notes_input.toPlainText().strip() or None
            else:
                c = Client(
                    name=name,
                    company=self.company_input.text().strip() or None,
                    email=email,
                    phone=self.phone_input.text().strip() or None,
                    address=self.address_input.toPlainText().strip() or None,
                    notes=self.notes_input.toPlainText().strip() or None
                )
                db.add(c)
                db.flush()

                act = Activity(
                    title="Client Registered",
                    description=f"{c.name} ({c.company or 'Individual'}) was added to the directory.",
                    icon="fa5s.user-plus",
                    category="client"
                )
                db.add(act)

            db.commit()
            self.accept()
        except Exception as e:
            db.rollback()
            self.show_error(f"Database error: {e}")
        finally:
            db.close()


# ============================================================================
# PROJECT DIALOG
# ============================================================================
class ProjectDialog(BaseModalDialog):
    """
    Form dialog to create or edit a project.
    """
    def __init__(self, project: Project = None, preselected_client_id: int = None, parent=None):
        title = "Edit Project" if project else "Create New Project"
        subtitle = "Update project scope & timeline" if project else "Initialize a new client engagement"
        super().__init__(title, subtitle, parent)
        self.project = project
        self.preselected_client_id = preselected_client_id
        self.client_ids = []
        self.resize(540, 620)

        self.init_form()
        if project:
            self.load_project_data()

        self.submit_btn.clicked.connect(self.save)

    def init_form(self):
        self.body_layout.addWidget(QLabel("Project Title *"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g. Nexus Mobile App Redesign")
        self.body_layout.addWidget(self.title_input)

        self.body_layout.addWidget(QLabel("Client *"))
        self.client_combo = QComboBox()
        self._populate_clients()
        self.body_layout.addWidget(self.client_combo)

        row1 = QHBoxLayout()
        row1.setSpacing(12)

        col_budget = QVBoxLayout()
        col_budget.addWidget(QLabel("Budget ($)"))
        self.budget_input = QLineEdit()
        self.budget_input.setPlaceholderText("e.g. 5000.00")
        col_budget.addWidget(self.budget_input)
        row1.addLayout(col_budget)

        col_status = QVBoxLayout()
        col_status.addWidget(QLabel("Status"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Not Started", "In Progress", "On Hold", "Completed", "Cancelled"])
        self.status_combo.setCurrentText("In Progress")
        col_status.addWidget(self.status_combo)
        row1.addLayout(col_status)

        self.body_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(12)

        col_deadline = QVBoxLayout()
        col_deadline.addWidget(QLabel("Deadline"))
        self.deadline_picker = QDateEdit()
        self.deadline_picker.setCalendarPopup(True)
        self.deadline_picker.setDate(QDate.currentDate().addDays(14))
        col_deadline.addWidget(self.deadline_picker)
        row2.addLayout(col_deadline)

        col_progress = QVBoxLayout()
        self.progress_lbl = QLabel("Progress: 0%")
        col_progress.addWidget(self.progress_lbl)
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 100)
        self.progress_slider.setValue(0)
        self.progress_slider.valueChanged.connect(lambda v: self.progress_lbl.setText(f"Progress: {v}%"))
        col_progress.addWidget(self.progress_slider)
        row2.addLayout(col_progress)

        self.body_layout.addLayout(row2)

        self.body_layout.addWidget(QLabel("Scope & Deliverables Description"))
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Detailed description of objectives, deliverables, milestones...")
        self.desc_input.setFixedHeight(85)
        self.body_layout.addWidget(self.desc_input)

    def _populate_clients(self):
        db = SessionLocal()
        try:
            clients = db.query(Client).all()
            self.client_combo.clear()
            self.client_ids = []
            select_idx = 0
            for idx, c in enumerate(clients):
                label = f"{c.name} ({c.company})" if c.company else c.name
                self.client_combo.addItem(label)
                self.client_ids.append(c.id)
                if self.preselected_client_id and c.id == self.preselected_client_id:
                    select_idx = idx

            if clients:
                self.client_combo.setCurrentIndex(select_idx)
        finally:
            db.close()

    def load_project_data(self):
        self.title_input.setText(self.project.title)
        if self.project.client_id in self.client_ids:
            self.client_combo.setCurrentIndex(self.client_ids.index(self.project.client_id))
        self.budget_input.setText(str(self.project.budget))
        self.status_combo.setCurrentText(self.project.status)
        if self.project.deadline:
            qdate = QDate(self.project.deadline.year, self.project.deadline.month, self.project.deadline.day)
            self.deadline_picker.setDate(qdate)
        self.progress_slider.setValue(self.project.progress)
        self.desc_input.setPlainText(self.project.description or "")

    def save(self):
        self.hide_error()
        title = self.title_input.text().strip()

        ok, err = validate_non_empty(title, "Project Title")
        if not ok:
            self.show_error(err)
            return

        if not self.client_ids:
            self.show_error("Please add at least one client first before creating a project.")
            return

        client_id = self.client_ids[self.client_combo.currentIndex()]

        ok, budget_val, err = validate_amount(self.budget_input.text(), "Budget")
        if not ok:
            self.show_error(err)
            return

        qdate = self.deadline_picker.date()
        deadline_dt = datetime(qdate.year(), qdate.month(), qdate.day(), 23, 59, 59)
        status = self.status_combo.currentText()
        progress = self.progress_slider.value()
        desc = self.desc_input.toPlainText().strip() or None

        db = SessionLocal()
        try:
            if self.project:
                p = db.query(Project).filter(Project.id == self.project.id).first()
                if p:
                    p.title = title
                    p.client_id = client_id
                    p.budget = budget_val
                    p.deadline = deadline_dt
                    p.status = status
                    p.progress = progress
                    p.description = desc
            else:
                p = Project(
                    title=title,
                    client_id=client_id,
                    budget=budget_val,
                    deadline=deadline_dt,
                    status=status,
                    progress=progress,
                    description=desc
                )
                db.add(p)
                db.flush()

                act = Activity(
                    title="New Project Started",
                    description=f"Project '{p.title}' was created with budget ${budget_val:,.2f}.",
                    icon="fa5s.folder-plus",
                    category="project"
                )
                db.add(act)

            db.commit()
            self.accept()
        except Exception as e:
            db.rollback()
            self.show_error(f"Database error: {e}")
        finally:
            db.close()


# ============================================================================
# TASK DIALOG
# ============================================================================
class TaskDialog(BaseModalDialog):
    """
    Form dialog to create or edit a task.
    """
    def __init__(self, task: Task = None, preselected_project_id: int = None, parent=None):
        title = "Edit Task" if task else "Create New Task"
        subtitle = "Update task milestone" if task else "Add a deliverable action item"
        super().__init__(title, subtitle, parent)
        self.task = task
        self.preselected_project_id = preselected_project_id
        self.project_ids = []
        self.resize(460, 420)

        self.init_form()
        if task:
            self.load_task_data()

        self.submit_btn.clicked.connect(self.save)

    def init_form(self):
        self.body_layout.addWidget(QLabel("Task Description / Title *"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g. Finalize Figma component tokens")
        self.body_layout.addWidget(self.title_input)

        self.body_layout.addWidget(QLabel("Associated Project"))
        self.project_combo = QComboBox()
        self._populate_projects()
        self.body_layout.addWidget(self.project_combo)

        row = QHBoxLayout()
        row.setSpacing(12)

        col_priority = QVBoxLayout()
        col_priority.addWidget(QLabel("Priority"))
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Low", "Medium", "High", "Urgent"])
        self.priority_combo.setCurrentText("Medium")
        col_priority.addWidget(self.priority_combo)
        row.addLayout(col_priority)

        col_deadline = QVBoxLayout()
        col_deadline.addWidget(QLabel("Due Date"))
        self.deadline_picker = QDateEdit()
        self.deadline_picker.setCalendarPopup(True)
        self.deadline_picker.setDate(QDate.currentDate().addDays(3))
        col_deadline.addWidget(self.deadline_picker)
        row.addLayout(col_deadline)

        self.body_layout.addLayout(row)

        self.completed_cb = QCheckBox("Mark task as completed")
        self.body_layout.addWidget(self.completed_cb)

    def _populate_projects(self):
        db = SessionLocal()
        try:
            projects = db.query(Project).all()
            self.project_combo.clear()
            self.project_combo.addItem("None (General Task)")
            self.project_ids = [None]

            select_idx = 0
            for idx, p in enumerate(projects):
                self.project_combo.addItem(p.title)
                self.project_ids.append(p.id)
                if self.preselected_project_id and p.id == self.preselected_project_id:
                    select_idx = idx + 1

            self.project_combo.setCurrentIndex(select_idx)
        finally:
            db.close()

    def load_task_data(self):
        self.title_input.setText(self.task.title)
        if self.task.project_id in self.project_ids:
            self.project_combo.setCurrentIndex(self.project_ids.index(self.task.project_id))
        self.priority_combo.setCurrentText(self.task.priority)
        if self.task.deadline:
            qdate = QDate(self.task.deadline.year, self.task.deadline.month, self.task.deadline.day)
            self.deadline_picker.setDate(qdate)
        self.completed_cb.setChecked(self.task.completed)

    def save(self):
        self.hide_error()
        title = self.title_input.text().strip()

        ok, err = validate_non_empty(title, "Task Title")
        if not ok:
            self.show_error(err)
            return

        project_id = self.project_ids[self.project_combo.currentIndex()]
        priority = self.priority_combo.currentText()
        qdate = self.deadline_picker.date()
        deadline_dt = datetime(qdate.year(), qdate.month(), qdate.day(), 18, 0, 0)
        completed = self.completed_cb.isChecked()

        db = SessionLocal()
        try:
            if self.task:
                t = db.query(Task).filter(Task.id == self.task.id).first()
                if t:
                    t.title = title
                    t.project_id = project_id
                    t.priority = priority
                    t.deadline = deadline_dt
                    t.completed = completed
            else:
                t = Task(
                    title=title,
                    project_id=project_id,
                    priority=priority,
                    deadline=deadline_dt,
                    completed=completed
                )
                db.add(t)

            db.commit()
            self.accept()
        except Exception as e:
            db.rollback()
            self.show_error(f"Database error: {e}")
        finally:
            db.close()


# ============================================================================
# INVOICE CREATION & EDITING DIALOG
# ============================================================================
class InvoiceDialog(BaseModalDialog):
    """
    Comprehensive invoice creator and editor with dynamic line items.
    """
    def __init__(self, invoice: Invoice = None, parent=None):
        title = "Edit Invoice" if invoice else "Create Invoice"
        subtitle = "Update billing details & line items" if invoice else "Generate a professional client invoice"
        super().__init__(title, subtitle, parent)
        self.invoice = invoice
        self.client_ids = []
        self.line_items = []
        self.resize(750, 720)

        self.init_form()
        if invoice:
            self.load_invoice_data()
        else:
            self._add_line_item("Professional Services", 1.0, 1500.0)

        self.submit_btn.clicked.connect(self.save)

    def init_form(self):
        # Top Meta Row: Client, Invoice #, Currency, Status
        meta_row1 = QHBoxLayout()
        meta_row1.setSpacing(12)

        col_client = QVBoxLayout()
        col_client.addWidget(QLabel("Client *"))
        self.client_combo = QComboBox()
        self._populate_clients()
        col_client.addWidget(self.client_combo)
        meta_row1.addLayout(col_client, 2)

        col_num = QVBoxLayout()
        col_num.addWidget(QLabel("Invoice Number *"))
        self.num_input = QLineEdit()
        self.num_input.setText(InvoiceService.generate_next_invoice_number())
        col_num.addWidget(self.num_input)
        meta_row1.addLayout(col_num, 1)

        col_curr = QVBoxLayout()
        col_curr.addWidget(QLabel("Currency"))
        self.curr_combo = QComboBox()
        self.curr_combo.addItems(["USD", "EUR", "GBP", "CAD", "AUD"])
        col_curr.addWidget(self.curr_combo)
        meta_row1.addLayout(col_curr, 1)

        self.body_layout.addLayout(meta_row1)

        # Dates & Status Row
        meta_row2 = QHBoxLayout()
        meta_row2.setSpacing(12)

        col_issue = QVBoxLayout()
        col_issue.addWidget(QLabel("Issue Date"))
        self.issue_picker = QDateEdit()
        self.issue_picker.setCalendarPopup(True)
        self.issue_picker.setDate(QDate.currentDate())
        col_issue.addWidget(self.issue_picker)
        meta_row2.addLayout(col_issue)

        col_due = QVBoxLayout()
        col_due.addWidget(QLabel("Due Date"))
        self.due_picker = QDateEdit()
        self.due_picker.setCalendarPopup(True)
        self.due_picker.setDate(QDate.currentDate().addDays(14))
        col_due.addWidget(self.due_picker)
        meta_row2.addLayout(col_due)

        col_status = QVBoxLayout()
        col_status.addWidget(QLabel("Status"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Draft", "Sent", "Paid", "Partially Paid", "Overdue", "Cancelled"])
        self.status_combo.setCurrentText("Sent")
        col_status.addWidget(self.status_combo)
        meta_row2.addLayout(col_status)

        self.body_layout.addLayout(meta_row2)

        # Line Items Section
        items_header = QHBoxLayout()
        items_header.addWidget(QLabel("<b>Line Items & Services</b>"))
        items_header.addStretch()

        add_item_btn = QPushButton(" + Add Line Item")
        add_item_btn.setCursor(Qt.PointingHandCursor)
        add_item_btn.setStyleSheet("""
            background: #2563EB20;
            color: #38BDF8;
            border: 1px solid #2563EB50;
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 12px;
        """)
        add_item_btn.clicked.connect(lambda: self._add_line_item())
        items_header.addWidget(add_item_btn)
        self.body_layout.addLayout(items_header)

        # Line items container
        self.items_container = QVBoxLayout()
        self.items_container.setSpacing(6)
        self.body_layout.addLayout(self.items_container)

        # Calculations Summary Box
        calc_box = QFrame()
        calc_box.setStyleSheet("""
            background: #181B22;
            border: 1px solid #282E3A;
            border-radius: 10px;
            padding: 12px;
        """)
        calc_layout = QHBoxLayout(calc_box)
        calc_layout.setSpacing(16)

        # Left notes
        notes_col = QVBoxLayout()
        notes_col.addWidget(QLabel("Notes & Payment Instructions:"))
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Direct deposit details, wire routing, thank you note...")
        self.notes_input.setFixedHeight(65)
        notes_col.addWidget(self.notes_input)
        calc_layout.addLayout(notes_col, 2)

        # Right totals
        totals_col = QVBoxLayout()
        totals_col.setSpacing(6)

        sub_row = QHBoxLayout()
        sub_row.addWidget(QLabel("Subtotal:"))
        self.subtotal_lbl = QLabel("$0.00")
        self.subtotal_lbl.setAlignment(Qt.AlignRight)
        sub_row.addWidget(self.subtotal_lbl)
        totals_col.addLayout(sub_row)

        disc_row = QHBoxLayout()
        disc_row.addWidget(QLabel("Discount ($):"))
        self.discount_input = QLineEdit("0.00")
        self.discount_input.setFixedWidth(80)
        self.discount_input.textChanged.connect(self.recalculate_totals)
        disc_row.addWidget(self.discount_input)
        totals_col.addLayout(disc_row)

        tax_row = QHBoxLayout()
        tax_row.addWidget(QLabel("Tax / VAT ($):"))
        self.tax_input = QLineEdit("0.00")
        self.tax_input.setFixedWidth(80)
        self.tax_input.textChanged.connect(self.recalculate_totals)
        tax_row.addWidget(self.tax_input)
        totals_col.addLayout(tax_row)

        tot_row = QHBoxLayout()
        tot_lbl = QLabel("<b>Total Due:</b>")
        tot_lbl.setStyleSheet("font-size: 14px;")
        tot_row.addWidget(tot_lbl)
        self.total_lbl = QLabel("$0.00")
        self.total_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.total_lbl.setStyleSheet("color: #38BDF8;")
        self.total_lbl.setAlignment(Qt.AlignRight)
        tot_row.addWidget(self.total_lbl)
        totals_col.addLayout(tot_row)

        calc_layout.addLayout(totals_col, 1)
        self.body_layout.addWidget(calc_box)

    def _populate_clients(self):
        db = SessionLocal()
        try:
            clients = db.query(Client).all()
            self.client_combo.clear()
            self.client_ids = []
            for c in clients:
                label = f"{c.name} ({c.company})" if c.company else c.name
                self.client_combo.addItem(label)
                self.client_ids.append(c.id)
        finally:
            db.close()

    def _add_line_item(self, desc: str = "", qty: float = 1.0, price: float = 0.0):
        item_row = QFrame()
        item_row.setStyleSheet("background: #1D2128; border: 1px solid #282E3A; border-radius: 8px; padding: 4px;")
        layout = QHBoxLayout(item_row)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        desc_input = QLineEdit(desc)
        desc_input.setPlaceholderText("Item description or service...")
        layout.addWidget(desc_input, 4)

        qty_input = QLineEdit(str(qty))
        qty_input.setPlaceholderText("Qty")
        qty_input.setFixedWidth(60)
        layout.addWidget(qty_input, 1)

        price_input = QLineEdit(f"{price:.2f}" if price else "0.00")
        price_input.setPlaceholderText("Price")
        price_input.setFixedWidth(90)
        layout.addWidget(price_input, 1)

        line_total_lbl = QLabel("$0.00")
        line_total_lbl.setFixedWidth(80)
        line_total_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        line_total_lbl.setStyleSheet("font-weight: bold; color: #F8FAFC;")
        layout.addWidget(line_total_lbl)

        del_btn = QPushButton()
        del_btn.setIcon(qta.icon("fa5s.trash-alt", color="#EF4444"))
        del_btn.setFixedSize(28, 28)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(del_btn)

        row_data = {
            "widget": item_row,
            "desc": desc_input,
            "qty": qty_input,
            "price": price_input,
            "total_lbl": line_total_lbl
        }
        self.line_items.append(row_data)

        # Hook recalculation
        qty_input.textChanged.connect(self.recalculate_totals)
        price_input.textChanged.connect(self.recalculate_totals)
        del_btn.clicked.connect(lambda: self._remove_line_item(row_data))

        self.items_container.addWidget(item_row)
        self.recalculate_totals()

    def _remove_line_item(self, row_data):
        if len(self.line_items) <= 1:
            QMessageBox.warning(self, "Warning", "An invoice must have at least one line item.")
            return

        self.line_items.remove(row_data)
        row_data["widget"].deleteLater()
        self.recalculate_totals()

    def recalculate_totals(self):
        subtotal = 0.0
        for item in self.line_items:
            try:
                qty = float(item["qty"].text().replace(",", "").strip() or 0)
                price = float(item["price"].text().replace(",", "").replace("$", "").strip() or 0)
                line_total = qty * price
                subtotal += line_total
                item["total_lbl"].setText(f"${line_total:,.2f}")
            except ValueError:
                item["total_lbl"].setText("$0.00")

        self.subtotal_lbl.setText(f"${subtotal:,.2f}")

        try:
            discount = float(self.discount_input.text().replace(",", "").replace("$", "").strip() or 0)
        except ValueError:
            discount = 0.0

        try:
            tax = float(self.tax_input.text().replace(",", "").replace("$", "").strip() or 0)
        except ValueError:
            tax = 0.0

        final_total = max(0.0, subtotal - discount + tax)
        self.total_lbl.setText(f"${final_total:,.2f}")

    def load_invoice_data(self):
        self.num_input.setText(self.invoice.invoice_number)
        if self.invoice.client_id in self.client_ids:
            self.client_combo.setCurrentIndex(self.client_ids.index(self.invoice.client_id))
        self.curr_combo.setCurrentText(self.invoice.currency)
        self.status_combo.setCurrentText(self.invoice.status)

        if self.invoice.issue_date:
            self.issue_picker.setDate(QDate(self.invoice.issue_date.year, self.invoice.issue_date.month, self.invoice.issue_date.day))
        if self.invoice.due_date:
            self.due_picker.setDate(QDate(self.invoice.due_date.year, self.invoice.due_date.month, self.invoice.due_date.day))

        self.discount_input.setText(f"{self.invoice.discount:.2f}")
        self.tax_input.setText(f"{self.invoice.tax:.2f}")
        self.notes_input.setPlainText(self.invoice.notes or "")

        # Clear default item and load items
        while self.line_items:
            item = self.line_items.pop(0)
            item["widget"].deleteLater()

        for it in self.invoice.items:
            self._add_line_item(it.description, it.quantity, it.unit_price)

    def save(self):
        self.hide_error()
        inv_num = self.num_input.text().strip()
        if not inv_num:
            self.show_error("Invoice Number is required.")
            return

        if not self.client_ids:
            self.show_error("Please add a client first before creating an invoice.")
            return

        client_id = self.client_ids[self.client_combo.currentIndex()]

        # Validate items
        items_payload = []
        for item in self.line_items:
            desc = item["desc"].text().strip()
            if not desc:
                self.show_error("All line items must have a description.")
                return

            try:
                qty = float(item["qty"].text().replace(",", "").strip())
                price = float(item["price"].text().replace(",", "").replace("$", "").strip())
                if qty <= 0 or price < 0:
                    self.show_error("Quantities and prices must be positive numbers.")
                    return
                items_payload.append({"description": desc, "quantity": qty, "unit_price": price, "total": qty * price})
            except ValueError:
                self.show_error("Invalid quantity or price format.")
                return

        subtotal = sum(i["total"] for i in items_payload)
        try:
            discount = float(self.discount_input.text().replace(",", "").replace("$", "").strip() or 0)
            tax = float(self.tax_input.text().replace(",", "").replace("$", "").strip() or 0)
        except ValueError:
            discount, tax = 0.0, 0.0

        total = max(0.0, subtotal - discount + tax)

        issue_q = self.issue_picker.date()
        due_q = self.due_picker.date()
        issue_dt = datetime(issue_q.year(), issue_q.month(), issue_q.day())
        due_dt = datetime(due_q.year(), due_q.month(), due_q.day(), 23, 59, 59)

        db = SessionLocal()
        try:
            if self.invoice:
                inv = db.query(Invoice).filter(Invoice.id == self.invoice.id).first()
                if inv:
                    inv.invoice_number = inv_num
                    inv.client_id = client_id
                    inv.currency = self.curr_combo.currentText()
                    inv.status = self.status_combo.currentText()
                    inv.issue_date = issue_dt
                    inv.due_date = due_dt
                    inv.subtotal = subtotal
                    inv.discount = discount
                    inv.tax = tax
                    inv.total = total
                    inv.notes = self.notes_input.toPlainText().strip() or None

                    # Replace items
                    db.query(InvoiceItem).filter(InvoiceItem.invoice_id == inv.id).delete()
                    for it in items_payload:
                        db.add(InvoiceItem(invoice_id=inv.id, **it))
            else:
                inv = Invoice(
                    invoice_number=inv_num,
                    client_id=client_id,
                    currency=self.curr_combo.currentText(),
                    status=self.status_combo.currentText(),
                    issue_date=issue_dt,
                    due_date=due_dt,
                    subtotal=subtotal,
                    discount=discount,
                    tax=tax,
                    total=total,
                    notes=self.notes_input.toPlainText().strip() or None
                )
                db.add(inv)
                db.flush()

                for it in items_payload:
                    db.add(InvoiceItem(invoice_id=inv.id, **it))

                act = Activity(
                    title="Invoice Created",
                    description=f"Generated {inv.invoice_number} for ${total:,.2f}.",
                    icon="fa5s.file-invoice-dollar",
                    category="invoice"
                )
                db.add(act)

            db.commit()
            self.accept()
        except Exception as e:
            db.rollback()
            self.show_error(f"Database error: {e}")
        finally:
            db.close()


# ============================================================================
# INVOICE DETAIL INSPECTOR DIALOG
# ============================================================================
class InvoiceDetailDialog(BaseModalDialog):
    """
    Invoice inspector with live PDF generation and payment status toggling.
    """
    def __init__(self, invoice_id: int, parent=None):
        db = SessionLocal()
        inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        db.close()

        title = f"Invoice {inv.invoice_number}" if inv else "Invoice Details"
        subtitle = f"Billed to {inv.client.name}" if inv and inv.client else "Invoice Overview"
        super().__init__(title, subtitle, parent)
        self.invoice_id = invoice_id
        self.resize(680, 580)

        # Custom action bar buttons
        self.submit_btn.setText("Edit Invoice")
        self.submit_btn.clicked.connect(self._open_edit)

        pdf_btn = QPushButton(" Export PDF")
        pdf_btn.setIcon(qta.icon("fa5s.file-pdf", color="#EF4444"))
        pdf_btn.setCursor(Qt.PointingHandCursor)
        pdf_btn.clicked.connect(self._export_pdf)
        self.actions_layout.insertWidget(0, pdf_btn)

        self.paid_btn = QPushButton(" Mark as Paid")
        self.paid_btn.setIcon(qta.icon("fa5s.check", color="#10B981"))
        self.paid_btn.setCursor(Qt.PointingHandCursor)
        self.paid_btn.clicked.connect(self._mark_paid)
        self.actions_layout.insertWidget(1, self.paid_btn)

        self.init_details()

    def init_details(self):
        db = SessionLocal()
        try:
            inv = db.query(Invoice).filter(Invoice.id == self.invoice_id).first()
            if not inv:
                self.show_error("Invoice not found.")
                return

            if inv.status == "Paid":
                self.paid_btn.setEnabled(False)
                self.paid_btn.setText("✓ Already Paid")

            # Meta Card
            card = QFrame()
            card.setStyleSheet("background: #181B22; border: 1px solid #282E3A; border-radius: 8px; padding: 12px;")
            card_layout = QGridLayout(card)

            card_layout.addWidget(QLabel("<b>Client:</b>"), 0, 0)
            card_layout.addWidget(QLabel(f"{inv.client.name} ({inv.client.company or 'Direct'})"), 0, 1)

            card_layout.addWidget(QLabel("<b>Issue Date:</b>"), 0, 2)
            card_layout.addWidget(QLabel(format_date(inv.issue_date)), 0, 3)

            card_layout.addWidget(QLabel("<b>Status:</b>"), 1, 0)
            card_layout.addWidget(StatusBadge(inv.status), 1, 1)

            card_layout.addWidget(QLabel("<b>Due Date:</b>"), 1, 2)
            card_layout.addWidget(QLabel(format_date(inv.due_date)), 1, 3)

            self.body_layout.addWidget(card)

            # Line items table
            table = QTableWidget()
            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(["Description", "Qty", "Unit Price", "Total"])
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
            table.verticalHeader().setVisible(False)
            table.setFixedHeight(180)

            table.setRowCount(len(inv.items))
            for r, item in enumerate(inv.items):
                table.setItem(r, 0, QTableWidgetItem(item.description))
                table.setItem(r, 1, QTableWidgetItem(f"{item.quantity:g}"))
                table.setItem(r, 2, QTableWidgetItem(format_currency(item.unit_price)))
                table.setItem(r, 3, QTableWidgetItem(format_currency(item.total)))

            self.body_layout.addWidget(table)

            # Totals
            totals_frame = QFrame()
            totals_layout = QHBoxLayout(totals_frame)
            totals_layout.addStretch()

            tot_lbl = QLabel(f"<b>Grand Total: {format_currency(inv.total)}</b>")
            tot_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
            tot_lbl.setStyleSheet("color: #38BDF8;")
            totals_layout.addWidget(tot_lbl)
            self.body_layout.addWidget(totals_frame)

        finally:
            db.close()

    def _mark_paid(self):
        InvoiceService.mark_status(self.invoice_id, "Paid")
        QMessageBox.information(self, "Success", "Invoice marked as Paid!")
        self.accept()

    def _export_pdf(self):
        db = SessionLocal()
        inv = db.query(Invoice).filter(Invoice.id == self.invoice_id).first()
        db.close()

        if not inv:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save PDF Invoice",
            f"{inv.invoice_number}.pdf",
            "PDF Files (*.pdf)"
        )
        if file_path:
            try:
                PDFService.generate_invoice_pdf(inv, file_path)
                reply = QMessageBox.question(
                    self,
                    "PDF Generated",
                    f"Invoice successfully exported to:\n{file_path}\n\nWould you like to open it now?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                if reply == QMessageBox.Yes:
                    QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
            except Exception as e:
                QMessageBox.critical(self, "PDF Export Error", f"Failed to generate PDF: {e}")

    def _open_edit(self):
        db = SessionLocal()
        inv = db.query(Invoice).filter(Invoice.id == self.invoice_id).first()
        db.close()
        if inv:
            diag = InvoiceDialog(inv, self)
            if diag.exec() == QDialog.Accepted:
                self.accept()


# ============================================================================
# EXPENSE DIALOG
# ============================================================================
class ExpenseDialog(BaseModalDialog):
    """
    Form dialog to record or edit business and project expenses.
    """
    def __init__(self, expense: Expense = None, parent=None):
        title = "Edit Expense" if expense else "Record Expense"
        subtitle = "Update expenditure item" if expense else "Log an operational or project expense"
        super().__init__(title, subtitle, parent)
        self.expense = expense
        self.project_ids = []
        self.resize(460, 430)

        self.init_form()
        if expense:
            self.load_expense_data()

        self.submit_btn.clicked.connect(self.save)

    def init_form(self):
        self.body_layout.addWidget(QLabel("Category *"))
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "Software & SaaS", "Hosting & Domains", "Assets & Typefaces",
            "Hardware & Gear", "Office & Desk", "Marketing & Ads", "Travel", "Other"
        ])
        self.body_layout.addWidget(self.category_combo)

        self.body_layout.addWidget(QLabel("Description *"))
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("e.g. Figma Organization Seat / Adobe CC")
        self.body_layout.addWidget(self.desc_input)

        row = QHBoxLayout()
        row.setSpacing(12)

        col_amt = QVBoxLayout()
        col_amt.addWidget(QLabel("Amount ($) *"))
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("e.g. 75.00")
        col_amt.addWidget(self.amount_input)
        row.addLayout(col_amt)

        col_date = QVBoxLayout()
        col_date.addWidget(QLabel("Date"))
        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(QDate.currentDate())
        col_date.addWidget(self.date_picker)
        row.addLayout(col_date)

        self.body_layout.addLayout(row)

        self.body_layout.addWidget(QLabel("Attach to Project (Optional)"))
        self.project_combo = QComboBox()
        self._populate_projects()
        self.body_layout.addWidget(self.project_combo)

    def _populate_projects(self):
        db = SessionLocal()
        try:
            projects = db.query(Project).all()
            self.project_combo.clear()
            self.project_combo.addItem("None (General Operating Expense)")
            self.project_ids = [None]
            for p in projects:
                self.project_combo.addItem(p.title)
                self.project_ids.append(p.id)
        finally:
            db.close()

    def load_expense_data(self):
        self.category_combo.setCurrentText(self.expense.category)
        self.desc_input.setText(self.expense.description)
        self.amount_input.setText(str(self.expense.amount))
        if self.expense.date:
            self.date_picker.setDate(QDate(self.expense.date.year, self.expense.date.month, self.expense.date.day))
        if self.expense.project_id in self.project_ids:
            self.project_combo.setCurrentIndex(self.project_ids.index(self.expense.project_id))

    def save(self):
        self.hide_error()
        desc = self.desc_input.text().strip()

        ok, err = validate_non_empty(desc, "Description")
        if not ok:
            self.show_error(err)
            return

        ok, amt, err = validate_amount(self.amount_input.text(), "Amount")
        if not ok or amt <= 0:
            self.show_error("Amount must be a positive number.")
            return

        qdate = self.date_picker.date()
        date_dt = datetime(qdate.year(), qdate.month(), qdate.day())
        category = self.category_combo.currentText()
        project_id = self.project_ids[self.project_combo.currentIndex()]

        db = SessionLocal()
        try:
            if self.expense:
                e = db.query(Expense).filter(Expense.id == self.expense.id).first()
                if e:
                    e.category = category
                    e.description = desc
                    e.amount = amt
                    e.date = date_dt
                    e.project_id = project_id
            else:
                e = Expense(
                    category=category,
                    description=desc,
                    amount=amt,
                    date=date_dt,
                    project_id=project_id
                )
                db.add(e)

            db.commit()
            self.accept()
        except Exception as e:
            db.rollback()
            self.show_error(f"Database error: {e}")
        finally:
            db.close()


# ============================================================================
# CLIENT DETAIL INSPECTOR DIALOG
# ============================================================================
class ClientDetailDialog(BaseModalDialog):
    """
    Detailed modal view for client history, projects, invoices, and notes.
    """
    def __init__(self, client_id: int, parent=None):
        db = SessionLocal()
        client = db.query(Client).filter(Client.id == client_id).first()
        db.close()

        title = client.name if client else "Client Details"
        subtitle = client.company or "Client Overview"
        super().__init__(title, subtitle, parent)
        self.client_id = client_id
        self.resize(650, 600)

        self.submit_btn.setText("Edit Client")
        self.submit_btn.clicked.connect(self._open_edit)

        self.init_details()

    def init_details(self):
        db = SessionLocal()
        try:
            client = db.query(Client).filter(Client.id == self.client_id).first()
            if not client:
                self.show_error("Client not found.")
                return

            info_frame = QFrame()
            info_frame.setStyleSheet("background: #181B22; border: 1px solid #282E3A; border-radius: 8px; padding: 12px;")
            info_layout = QVBoxLayout(info_frame)
            info_layout.setSpacing(6)

            info_layout.addWidget(QLabel(f"<b>Email:</b> {client.email}"))
            info_layout.addWidget(QLabel(f"<b>Phone:</b> {client.phone or 'Not provided'}"))
            info_layout.addWidget(QLabel(f"<b>Address:</b> {client.address or 'Not provided'}"))
            if client.notes:
                info_layout.addWidget(QLabel(f"<b>Notes:</b> {client.notes}"))

            self.body_layout.addWidget(info_frame)

            self.body_layout.addWidget(QLabel(f"<b>Associated Projects ({len(client.projects)})</b>"))
            proj_table = QTableWidget()
            proj_table.setColumnCount(4)
            proj_table.setHorizontalHeaderLabels(["Project", "Budget", "Deadline", "Status"])
            proj_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            proj_table.verticalHeader().setVisible(False)
            proj_table.setFixedHeight(140)

            proj_table.setRowCount(len(client.projects))
            for r, p in enumerate(client.projects):
                proj_table.setItem(r, 0, QTableWidgetItem(p.title))
                proj_table.setItem(r, 1, QTableWidgetItem(format_currency(p.budget)))
                proj_table.setItem(r, 2, QTableWidgetItem(format_date(p.deadline) if p.deadline else "—"))
                proj_table.setItem(r, 3, QTableWidgetItem(p.status))
            self.body_layout.addWidget(proj_table)

            self.body_layout.addWidget(QLabel(f"<b>Invoices ({len(client.invoices)})</b>"))
            inv_table = QTableWidget()
            inv_table.setColumnCount(4)
            inv_table.setHorizontalHeaderLabels(["Invoice #", "Date", "Total", "Status"])
            inv_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            inv_table.verticalHeader().setVisible(False)
            inv_table.setFixedHeight(140)

            inv_table.setRowCount(len(client.invoices))
            for r, inv in enumerate(client.invoices):
                inv_table.setItem(r, 0, QTableWidgetItem(inv.invoice_number))
                inv_table.setItem(r, 1, QTableWidgetItem(format_date(inv.issue_date)))
                inv_table.setItem(r, 2, QTableWidgetItem(format_currency(inv.total)))
                inv_table.setItem(r, 3, QTableWidgetItem(inv.status))
            self.body_layout.addWidget(inv_table)

        finally:
            db.close()

    def _open_edit(self):
        db = SessionLocal()
        client = db.query(Client).filter(Client.id == self.client_id).first()
        db.close()
        if client:
            diag = ClientDialog(client, self)
            if diag.exec() == QDialog.Accepted:
                self.accept()


# ============================================================================
# TEMPLATE CREATION & EDITING DIALOG
# ============================================================================
class TemplateDialog(BaseModalDialog):
    """
    Form dialog to create or edit reusable templates.
    """
    def __init__(self, template: Template = None, parent=None):
        title = "Edit Template" if template else "Create New Template"
        subtitle = "Update reusable document boilerplate" if template else "Add a reusable proposal or email template"
        super().__init__(title, subtitle, parent)
        self.template = template
        self.resize(580, 520)

        self.init_form()
        if template:
            self.load_template_data()

        self.submit_btn.clicked.connect(self.save)

    def init_form(self):
        self.body_layout.addWidget(QLabel("Template Title *"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g. Scope Creep Revision Agreement")
        self.body_layout.addWidget(self.title_input)

        self.body_layout.addWidget(QLabel("Category *"))
        self.cat_combo = QComboBox()
        self.cat_combo.addItems(["Proposals", "Emails & Outreach", "Quotations", "SEO", "Invoices", "General"])
        self.body_layout.addWidget(self.cat_combo)

        self.body_layout.addWidget(QLabel("Template Body / Content *"))
        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("Enter template text. You can use placeholders like [Client Name], [Project Title]...")
        self.content_input.setFixedHeight(220)
        self.body_layout.addWidget(self.content_input)

    def load_template_data(self):
        self.title_input.setText(self.template.title)
        self.cat_combo.setCurrentText(self.template.category)
        self.content_input.setPlainText(self.template.content)

    def save(self):
        self.hide_error()
        title = self.title_input.text().strip()
        content = self.content_input.toPlainText().strip()

        ok, err = validate_non_empty(title, "Template Title")
        if not ok:
            self.show_error(err)
            return

        ok, err = validate_non_empty(content, "Template Content")
        if not ok:
            self.show_error(err)
            return

        category = self.cat_combo.currentText()

        db = SessionLocal()
        try:
            if self.template:
                t = db.query(Template).filter(Template.id == self.template.id).first()
                if t:
                    t.title = title
                    t.category = category
                    t.content = content
            else:
                t = Template(
                    title=title,
                    category=category,
                    content=content
                )
                db.add(t)

            db.commit()
            self.accept()
        except Exception as e:
            db.rollback()
            self.show_error(f"Database error: {e}")
        finally:
            db.close()

