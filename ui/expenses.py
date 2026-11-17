"""
Expense Management View for FreelancePilot.
Supports logging expenditures, project cost tracking, category filtering, and net profit calculations.
"""

from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QComboBox, QFrame,
    QMessageBox, QDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import qtawesome as qta

from database.db import SessionLocal
from database.models import Expense, Project, Invoice
from components.dialogs import ExpenseDialog
from components.cards import StatCard
from utils.helpers import format_currency, format_date


class ExpensesView(QWidget):
    """
    Expense Tracking and Profit Management Screen.
    """
    data_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.expenses = []
        self.init_ui()
        self.load_expenses()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 32)
        layout.setSpacing(20)

        # 1. Header Banner
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Expense Management")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #F8FAFC;")
        sub = QLabel("Record business expenditures, software subscriptions, hosting fees, and project costs.")
        sub.setFont(QFont("Segoe UI", 10))
        sub.setStyleSheet("color: #94A3B8;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        header.addStretch()

        self.add_btn = QPushButton(" + Record Expense")
        self.add_btn.setObjectName("primaryButton")
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.clicked.connect(self.open_add_dialog)
        header.addWidget(self.add_btn)
        layout.addLayout(header)

        # 2. Stats Strip
        self.stats_row = QHBoxLayout()
        self.stats_row.setSpacing(14)

        self.stat_total = StatCard("TOTAL EXPENSES", "$0.00", "fa5s.receipt", "All-time costs", False, "#EF4444")
        self.stat_monthly = StatCard("THIS MONTH", "$0.00", "fa5s.calendar-alt", "Current billing cycle", False, "#F59E0B")
        self.stat_net_profit = StatCard("NET PROFIT", "$0.00", "fa5s.chart-line", "Gross Revenue - Expenses", True, "#10B981")

        self.stats_row.addWidget(self.stat_total)
        self.stats_row.addWidget(self.stat_monthly)
        self.stats_row.addWidget(self.stat_net_profit)
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
        self.search_box.setPlaceholderText("Search expenses by description or category...")
        self.search_box.setStyleSheet("background: transparent; border: none; color: #F8FAFC;")
        self.search_box.textChanged.connect(self.filter_expenses)
        s_layout.addWidget(self.search_box)
        action_bar.addWidget(search_frame, 1)

        # Category filter dropdown
        cat_lbl = QLabel("Category:")
        cat_lbl.setStyleSheet("color: #94A3B8; font-weight: 500;")
        action_bar.addWidget(cat_lbl)

        self.cat_filter = QComboBox()
        self.cat_filter.addItems([
            "All Categories", "Software & SaaS", "Hosting & Domains", "Assets & Typefaces",
            "Hardware & Gear", "Office & Desk", "Marketing & Ads", "Travel", "Other"
        ])
        self.cat_filter.setFixedWidth(160)
        self.cat_filter.currentTextChanged.connect(lambda _: self.filter_expenses())
        action_bar.addWidget(self.cat_filter)

        refresh_btn = QPushButton(" Refresh")
        refresh_btn.setIcon(qta.icon("fa5s.sync", color="#94A3B8"))
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.load_expenses)
        action_bar.addWidget(refresh_btn)

        layout.addLayout(action_bar)

        # 4. Expenses Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Date", "Category", "Description", "Project", "Amount", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table, 1)

    def load_expenses(self):
        db = SessionLocal()
        try:
            self.expenses = db.query(Expense).order_by(Expense.date.desc()).all()
            self.display_expenses(self.expenses)

            # Calculate stats
            now = datetime.now()
            total_exp = sum(e.amount for e in self.expenses)
            month_exp = sum(
                e.amount for e in self.expenses
                if e.date and e.date.month == now.month and e.date.year == now.year
            )

            # Total collected revenue
            paid_invoices = db.query(Invoice).filter(Invoice.status == "Paid").all()
            total_rev = sum(inv.total for inv in paid_invoices)
            net_profit = total_rev - total_exp

            self.stat_total.update_value(format_currency(total_exp))
            self.stat_monthly.update_value(format_currency(month_exp))
            self.stat_net_profit.update_value(format_currency(net_profit))
        finally:
            db.close()

    def display_expenses(self, expenses):
        self.table.setRowCount(len(expenses))
        for row, exp in enumerate(expenses):
            self.table.setItem(row, 0, QTableWidgetItem(format_date(exp.date)))
            self.table.setItem(row, 1, QTableWidgetItem(exp.category))
            self.table.setItem(row, 2, QTableWidgetItem(exp.description))

            proj_title = exp.project.title if exp.project else "General Overhead"
            self.table.setItem(row, 3, QTableWidgetItem(proj_title))

            amt_item = QTableWidgetItem(format_currency(exp.amount))
            amt_item.setForeground(Qt.red)
            self.table.setItem(row, 4, amt_item)

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(6, 2, 6, 2)
            actions_layout.setSpacing(6)

            edit_btn = QPushButton()
            edit_btn.setIcon(qta.icon("fa5s.edit", color="#F59E0B"))
            edit_btn.setToolTip("Edit Expense")
            edit_btn.setFixedSize(28, 28)
            edit_btn.setCursor(Qt.PointingHandCursor)
            edit_btn.clicked.connect(lambda _, expense_obj=exp: self.open_edit_dialog(expense_obj))
            actions_layout.addWidget(edit_btn)

            del_btn = QPushButton()
            del_btn.setIcon(qta.icon("fa5s.trash-alt", color="#EF4444"))
            del_btn.setToolTip("Delete Expense")
            del_btn.setFixedSize(28, 28)
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.clicked.connect(lambda _, eid=exp.id, edesc=exp.description: self.delete_expense(eid, edesc))
            actions_layout.addWidget(del_btn)

            self.table.setCellWidget(row, 5, actions_widget)

    def filter_expenses(self):
        query = self.search_box.text().lower().strip()
        cat_filter = self.cat_filter.currentText()

        filtered = self.expenses
        if cat_filter != "All Categories":
            filtered = [e for e in filtered if e.category == cat_filter]

        if query:
            filtered = [
                e for e in filtered
                if query in e.description.lower() or query in e.category.lower() or
                (e.project and query in e.project.title.lower())
            ]

        self.display_expenses(filtered)

    def open_add_dialog(self):
        diag = ExpenseDialog(parent=self)
        if diag.exec() == QDialog.Accepted:
            self.load_expenses()
            self.data_changed.emit()

    def open_edit_dialog(self, expense: Expense):
        diag = ExpenseDialog(expense=expense, parent=self)
        if diag.exec() == QDialog.Accepted:
            self.load_expenses()
            self.data_changed.emit()

    def delete_expense(self, expense_id: int, description: str):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete expense '{description}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            db = SessionLocal()
            try:
                exp = db.query(Expense).filter(Expense.id == expense_id).first()
                if exp:
                    db.delete(exp)
                    db.commit()
                    self.load_expenses()
                    self.data_changed.emit()
            except Exception as e:
                db.rollback()
                QMessageBox.critical(self, "Error", f"Failed to delete expense: {e}")
            finally:
                db.close()
