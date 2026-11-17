"""
Project Management View for FreelancePilot.
Supports creating, editing, filtering, and tracking client projects and progress.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QComboBox, QFrame,
    QProgressBar, QMessageBox, QDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import qtawesome as qta

from database.db import SessionLocal
from database.models import Project, Client, Task
from components.dialogs import ProjectDialog
from components.cards import StatCard, StatusBadge
from utils.helpers import format_currency, format_date


class ProjectsView(QWidget):
    """
    Project Tracker and Management Screen.
    """
    data_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.projects = []
        self.init_ui()
        self.load_projects()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 32)
        layout.setSpacing(20)

        # 1. Header Banner
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Project Engagements")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #F8FAFC;")
        sub = QLabel("Oversee deliverables, client milestones, budgets, and project delivery deadlines.")
        sub.setFont(QFont("Segoe UI", 10))
        sub.setStyleSheet("color: #94A3B8;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        header.addStretch()

        self.add_btn = QPushButton(" + New Project")
        self.add_btn.setObjectName("primaryButton")
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.clicked.connect(self.open_add_dialog)
        header.addWidget(self.add_btn)
        layout.addLayout(header)

        # 2. Stats Strip
        self.stats_row = QHBoxLayout()
        self.stats_row.setSpacing(14)

        self.stat_total = StatCard("TOTAL PROJECTS", "0", "fa5s.layer-group", "All engagements", True, "#3B82F6")
        self.stat_active = StatCard("IN PROGRESS", "0", "fa5s.spinner", "Active delivery", True, "#10B981")
        self.stat_pipeline = StatCard("PIPELINE BUDGET", "$0.00", "fa5s.dollar-sign", "Total project budgets", True, "#8B5CF6")

        self.stats_row.addWidget(self.stat_total)
        self.stats_row.addWidget(self.stat_active)
        self.stats_row.addWidget(self.stat_pipeline)
        layout.addLayout(self.stats_row)

        # 3. Filter & Search Bar
        action_bar = QHBoxLayout()
        action_bar.setSpacing(12)

        # Search box
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
        self.search_box.setPlaceholderText("Search projects by title, client, or scope...")
        self.search_box.setStyleSheet("background: transparent; border: none; color: #F8FAFC;")
        self.search_box.textChanged.connect(self.filter_projects)
        s_layout.addWidget(self.search_box)
        action_bar.addWidget(search_frame, 1)

        # Status filter dropdown
        status_lbl = QLabel("Status:")
        status_lbl.setStyleSheet("color: #94A3B8; font-weight: 500;")
        action_bar.addWidget(status_lbl)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Statuses", "In Progress", "Not Started", "On Hold", "Completed", "Cancelled"])
        self.status_filter.setFixedWidth(140)
        self.status_filter.currentTextChanged.connect(lambda _: self.filter_projects())
        action_bar.addWidget(self.status_filter)

        refresh_btn = QPushButton(" Refresh")
        refresh_btn.setIcon(qta.icon("fa5s.sync", color="#94A3B8"))
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.load_projects)
        action_bar.addWidget(refresh_btn)

        layout.addLayout(action_bar)

        # 4. Projects Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Project Title", "Client", "Budget", "Deadline", "Status", "Progress", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table, 1)

    def load_projects(self):
        db = SessionLocal()
        try:
            self.projects = db.query(Project).all()
            self.display_projects(self.projects)

            # Update stats
            total_count = len(self.projects)
            active_count = sum(1 for p in self.projects if p.status == "In Progress")
            total_budget = sum(p.budget for p in self.projects)

            self.stat_total.update_value(str(total_count))
            self.stat_active.update_value(str(active_count))
            self.stat_pipeline.update_value(format_currency(total_budget))
        finally:
            db.close()

    def display_projects(self, projects):
        self.table.setRowCount(len(projects))
        for row, p in enumerate(projects):
            # Title
            self.table.setItem(row, 0, QTableWidgetItem(p.title))

            # Client
            client_name = p.client.company or p.client.name if p.client else "—"
            self.table.setItem(row, 1, QTableWidgetItem(client_name))

            # Budget
            self.table.setItem(row, 2, QTableWidgetItem(format_currency(p.budget)))

            # Deadline
            self.table.setItem(row, 3, QTableWidgetItem(format_date(p.deadline) if p.deadline else "No due date"))

            # Status Badge widget
            status_container = QWidget()
            s_layout = QHBoxLayout(status_container)
            s_layout.setContentsMargins(4, 2, 4, 2)
            s_layout.setAlignment(Qt.AlignCenter)
            badge = StatusBadge(p.status)
            s_layout.addWidget(badge)
            self.table.setCellWidget(row, 4, status_container)

            # Progress Bar widget
            progress_widget = QWidget()
            p_layout = QHBoxLayout(progress_widget)
            p_layout.setContentsMargins(6, 2, 6, 2)
            pbar = QProgressBar()
            pbar.setValue(p.progress)
            pbar.setFixedWidth(80)
            pbar.setFixedHeight(6)
            pbar.setTextVisible(False)
            p_layout.addWidget(pbar)

            p_lbl = QLabel(f"{p.progress}%")
            p_lbl.setStyleSheet("color: #94A3B8; font-size: 11px;")
            p_layout.addWidget(p_lbl)
            self.table.setCellWidget(row, 5, progress_widget)

            # Actions widget
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(6, 2, 6, 2)
            actions_layout.setSpacing(6)

            edit_btn = QPushButton()
            edit_btn.setIcon(qta.icon("fa5s.edit", color="#F59E0B"))
            edit_btn.setToolTip("Edit Project")
            edit_btn.setFixedSize(28, 28)
            edit_btn.setCursor(Qt.PointingHandCursor)
            edit_btn.clicked.connect(lambda _, proj=p: self.open_edit_dialog(proj))
            actions_layout.addWidget(edit_btn)

            del_btn = QPushButton()
            del_btn.setIcon(qta.icon("fa5s.trash-alt", color="#EF4444"))
            del_btn.setToolTip("Delete Project")
            del_btn.setFixedSize(28, 28)
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.clicked.connect(lambda _, pid=p.id, ptitle=p.title: self.delete_project(pid, ptitle))
            actions_layout.addWidget(del_btn)

            self.table.setCellWidget(row, 6, actions_widget)

    def filter_projects(self):
        query = self.search_box.text().lower().strip()
        status_filter = self.status_filter.currentText()

        filtered = self.projects
        if status_filter != "All Statuses":
            filtered = [p for p in filtered if p.status == status_filter]

        if query:
            filtered = [
                p for p in filtered
                if query in p.title.lower() or
                (p.client and (query in p.client.name.lower() or query in (p.client.company or "").lower())) or
                (p.description and query in p.description.lower())
            ]

        self.display_projects(filtered)

    def open_add_dialog(self):
        dialog = ProjectDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.load_projects()
            self.data_changed.emit()

    def open_edit_dialog(self, project: Project):
        dialog = ProjectDialog(project=project, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.load_projects()
            self.data_changed.emit()

    def delete_project(self, project_id: int, title: str):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete project '{title}'?\n\n"
            "This will also delete associated tasks.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            db = SessionLocal()
            try:
                p = db.query(Project).filter(Project.id == project_id).first()
                if p:
                    db.delete(p)
                    db.commit()
                    self.load_projects()
                    self.data_changed.emit()
            except Exception as e:
                db.rollback()
                QMessageBox.critical(self, "Error", f"Failed to delete project: {e}")
            finally:
                db.close()
