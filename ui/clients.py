"""
Client Management View for FreelancePilot.
Supports adding, editing, deleting, searching, filtering, and viewing client histories.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QFrame, QMessageBox, QDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import qtawesome as qta

from database.db import SessionLocal
from database.models import Client, Project, Invoice, Activity
from components.dialogs import ClientDialog, ClientDetailDialog
from components.cards import StatCard
from utils.helpers import format_currency


class ClientsView(QWidget):
    """
    Client CRM Screen.
    """
    data_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.clients = []
        self.init_ui()
        self.load_clients()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 32)
        layout.setSpacing(20)

        # 1. Header Banner
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Client Directory")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #F8FAFC;")
        sub = QLabel("Manage your client directory, communications, and project history.")
        sub.setFont(QFont("Segoe UI", 10))
        sub.setStyleSheet("color: #94A3B8;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        header.addStretch()

        self.add_btn = QPushButton(" + Add Client")
        self.add_btn.setObjectName("primaryButton")
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.clicked.connect(self.open_add_dialog)
        header.addWidget(self.add_btn)
        layout.addLayout(header)

        # 2. Stats Strip
        self.stats_row = QHBoxLayout()
        self.stats_row.setSpacing(14)

        self.stat_total = StatCard("TOTAL CLIENTS", "0", "fa5s.users", "In database", True, "#3B82F6")
        self.stat_active = StatCard("ACTIVE CLIENTS", "0", "fa5s.briefcase", "With open projects", True, "#10B981")
        self.stat_revenue = StatCard("TOTAL BILLED", "$0.00", "fa5s.file-invoice-dollar", "Across all clients", True, "#8B5CF6")

        self.stats_row.addWidget(self.stat_total)
        self.stats_row.addWidget(self.stat_active)
        self.stats_row.addWidget(self.stat_revenue)
        layout.addLayout(self.stats_row)

        # 3. Search and Action Bar
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
        self.search_box.setPlaceholderText("Search clients by name, company, or email...")
        self.search_box.setStyleSheet("background: transparent; border: none; color: #F8FAFC;")
        self.search_box.textChanged.connect(self.filter_clients)
        s_layout.addWidget(self.search_box)
        action_bar.addWidget(search_frame, 1)

        refresh_btn = QPushButton(" Refresh")
        refresh_btn.setIcon(qta.icon("fa5s.sync", color="#94A3B8"))
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.load_clients)
        action_bar.addWidget(refresh_btn)

        layout.addLayout(action_bar)

        # 4. Clients Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Name", "Company", "Email", "Phone", "Projects", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.cellDoubleClicked.connect(self.on_row_double_click)
        layout.addWidget(self.table, 1)

    def load_clients(self):
        db = SessionLocal()
        try:
            self.clients = db.query(Client).all()
            self.display_clients(self.clients)

            # Update stats
            total_count = len(self.clients)
            active_count = sum(1 for c in self.clients if any(p.status == "In Progress" for p in c.projects))

            all_invoices = db.query(Invoice).filter(Invoice.status == "Paid").all()
            total_rev = sum(inv.total for inv in all_invoices)

            self.stat_total.update_value(str(total_count))
            self.stat_active.update_value(str(active_count))
            self.stat_revenue.update_value(format_currency(total_rev))
        finally:
            db.close()

    def display_clients(self, clients):
        self.table.setRowCount(len(clients))
        for row, c in enumerate(clients):
            self.table.setItem(row, 0, QTableWidgetItem(c.name))
            self.table.setItem(row, 1, QTableWidgetItem(c.company or "—"))
            self.table.setItem(row, 2, QTableWidgetItem(c.email))
            self.table.setItem(row, 3, QTableWidgetItem(c.phone or "—"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{len(c.projects)} Projects"))

            # Actions Container
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(6, 2, 6, 2)
            actions_layout.setSpacing(6)

            view_btn = QPushButton()
            view_btn.setIcon(qta.icon("fa5s.eye", color="#38BDF8"))
            view_btn.setToolTip("View Client Details")
            view_btn.setFixedSize(28, 28)
            view_btn.setCursor(Qt.PointingHandCursor)
            view_btn.clicked.connect(lambda _, cid=c.id: self.open_detail_dialog(cid))
            actions_layout.addWidget(view_btn)

            edit_btn = QPushButton()
            edit_btn.setIcon(qta.icon("fa5s.edit", color="#F59E0B"))
            edit_btn.setToolTip("Edit Client")
            edit_btn.setFixedSize(28, 28)
            edit_btn.setCursor(Qt.PointingHandCursor)
            edit_btn.clicked.connect(lambda _, client_obj=c: self.open_edit_dialog(client_obj))
            actions_layout.addWidget(edit_btn)

            del_btn = QPushButton()
            del_btn.setIcon(qta.icon("fa5s.trash-alt", color="#EF4444"))
            del_btn.setToolTip("Delete Client")
            del_btn.setFixedSize(28, 28)
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.clicked.connect(lambda _, cid=c.id, cname=c.name: self.delete_client(cid, cname))
            actions_layout.addWidget(del_btn)

            self.table.setCellWidget(row, 5, actions_widget)

    def filter_clients(self, text: str):
        query = text.lower().strip()
        if not query:
            self.display_clients(self.clients)
            return

        filtered = [
            c for c in self.clients
            if query in c.name.lower() or query in (c.company or "").lower() or query in c.email.lower()
        ]
        self.display_clients(filtered)

    def open_add_dialog(self):
        dialog = ClientDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.load_clients()
            self.data_changed.emit()

    def open_edit_dialog(self, client: Client):
        dialog = ClientDialog(client=client, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.load_clients()
            self.data_changed.emit()

    def open_detail_dialog(self, client_id: int):
        dialog = ClientDetailDialog(client_id=client_id, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.load_clients()
            self.data_changed.emit()

    def on_row_double_click(self, row, column):
        if row < len(self.clients):
            self.open_detail_dialog(self.clients[row].id)

    def delete_client(self, client_id: int, client_name: str):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete client '{client_name}'?\n\n"
            "This will permanently delete this client and all associated projects and tasks.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            db = SessionLocal()
            try:
                c = db.query(Client).filter(Client.id == client_id).first()
                if c:
                    db.delete(c)
                    db.commit()
                    self.load_clients()
                    self.data_changed.emit()
            except Exception as e:
                db.rollback()
                QMessageBox.critical(self, "Error", f"Failed to delete client: {e}")
            finally:
                db.close()
