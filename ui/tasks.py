"""
Task Management View for FreelancePilot.
Supports interactive task checklist, priority tagging, overdue indicators, and project linking.
"""

from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QComboBox, QFrame,
    QCheckBox, QMessageBox, QDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import qtawesome as qta

from database.db import SessionLocal
from database.models import Task, Project
from components.dialogs import TaskDialog
from components.cards import StatCard, StatusBadge
from utils.helpers import format_date, get_relative_date_string


class TasksView(QWidget):
    """
    Task Management Screen with live interactive checkboxes.
    """
    data_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks = []
        self.init_ui()
        self.load_tasks()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 32)
        layout.setSpacing(20)

        # 1. Header Banner
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Tasks & Deliverables")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #F8FAFC;")
        sub = QLabel("Track actionable tasks, client deliverables, sprints, and completion deadlines.")
        sub.setFont(QFont("Segoe UI", 10))
        sub.setStyleSheet("color: #94A3B8;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        header.addStretch()

        self.add_btn = QPushButton(" + Add Task")
        self.add_btn.setObjectName("primaryButton")
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.clicked.connect(self.open_add_dialog)
        header.addWidget(self.add_btn)
        layout.addLayout(header)

        # 2. Stats Strip
        self.stats_row = QHBoxLayout()
        self.stats_row.setSpacing(14)

        self.stat_pending = StatCard("PENDING TASKS", "0", "fa5s.tasks", "To be completed", True, "#F59E0B")
        self.stat_urgent = StatCard("URGENT / OVERDUE", "0", "fa5s.exclamation-circle", "Requires attention", False, "#EF4444")
        self.stat_completed = StatCard("COMPLETED", "0", "fa5s.check-circle", "Finished tasks", True, "#10B981")

        self.stats_row.addWidget(self.stat_pending)
        self.stats_row.addWidget(self.stat_urgent)
        self.stats_row.addWidget(self.stat_completed)
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
        self.search_box.setPlaceholderText("Search tasks or projects...")
        self.search_box.setStyleSheet("background: transparent; border: none; color: #F8FAFC;")
        self.search_box.textChanged.connect(self.filter_tasks)
        s_layout.addWidget(self.search_box)
        action_bar.addWidget(search_frame, 1)

        # Status filter
        status_lbl = QLabel("Status:")
        status_lbl.setStyleSheet("color: #94A3B8; font-weight: 500;")
        action_bar.addWidget(status_lbl)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Tasks", "Pending Only", "Completed Only", "Overdue Only"])
        self.status_filter.setFixedWidth(130)
        self.status_filter.currentTextChanged.connect(lambda _: self.filter_tasks())
        action_bar.addWidget(self.status_filter)

        # Priority filter
        prio_lbl = QLabel("Priority:")
        prio_lbl.setStyleSheet("color: #94A3B8; font-weight: 500;")
        action_bar.addWidget(prio_lbl)

        self.prio_filter = QComboBox()
        self.prio_filter.addItems(["All Priorities", "Urgent", "High", "Medium", "Low"])
        self.prio_filter.setFixedWidth(130)
        self.prio_filter.currentTextChanged.connect(lambda _: self.filter_tasks())
        action_bar.addWidget(self.prio_filter)

        refresh_btn = QPushButton(" Refresh")
        refresh_btn.setIcon(qta.icon("fa5s.sync", color="#94A3B8"))
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.load_tasks)
        action_bar.addWidget(refresh_btn)

        layout.addLayout(action_bar)

        # 4. Tasks Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Done", "Task Description", "Project", "Priority", "Due Date", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table, 1)

    def load_tasks(self):
        db = SessionLocal()
        try:
            self.tasks = db.query(Task).order_by(Task.completed.asc(), Task.deadline.asc()).all()
            self.display_tasks(self.tasks)

            # Update stats
            now = datetime.now()
            pending_count = sum(1 for t in self.tasks if not t.completed)
            urgent_count = sum(
                1 for t in self.tasks
                if not t.completed and (t.priority == "Urgent" or (t.deadline and t.deadline < now))
            )
            completed_count = sum(1 for t in self.tasks if t.completed)

            self.stat_pending.update_value(str(pending_count))
            self.stat_urgent.update_value(str(urgent_count))
            self.stat_completed.update_value(str(completed_count))
        finally:
            db.close()

    def display_tasks(self, tasks):
        self.table.setRowCount(len(tasks))
        now = datetime.now()

        for row, t in enumerate(tasks):
            # Checkbox widget
            cb_container = QWidget()
            cb_layout = QHBoxLayout(cb_container)
            cb_layout.setContentsMargins(6, 2, 6, 2)
            cb_layout.setAlignment(Qt.AlignCenter)
            cb = QCheckBox()
            cb.setChecked(t.completed)
            cb.stateChanged.connect(lambda state, tid=t.id: self.toggle_task_completion(tid, state == Qt.Checked))
            cb_layout.addWidget(cb)
            self.table.setCellWidget(row, 0, cb_container)

            # Title
            title_item = QTableWidgetItem(t.title)
            if t.completed:
                title_item.setForeground(Qt.gray)
            self.table.setItem(row, 1, title_item)

            # Project
            proj_name = t.project.title if t.project else "General"
            self.table.setItem(row, 2, QTableWidgetItem(proj_name))

            # Priority Badge
            prio_container = QWidget()
            prio_layout = QHBoxLayout(prio_container)
            prio_layout.setContentsMargins(4, 2, 4, 2)
            prio_layout.setAlignment(Qt.AlignCenter)
            badge = StatusBadge(t.priority)
            prio_layout.addWidget(badge)
            self.table.setCellWidget(row, 3, prio_container)

            # Due Date
            due_str = get_relative_date_string(t.deadline) if t.deadline else "No due date"
            due_item = QTableWidgetItem(due_str)
            if not t.completed and t.deadline and t.deadline < now:
                due_item.setForeground(Qt.red)
            self.table.setItem(row, 4, due_item)

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(6, 2, 6, 2)
            actions_layout.setSpacing(6)

            edit_btn = QPushButton()
            edit_btn.setIcon(qta.icon("fa5s.edit", color="#F59E0B"))
            edit_btn.setToolTip("Edit Task")
            edit_btn.setFixedSize(28, 28)
            edit_btn.setCursor(Qt.PointingHandCursor)
            edit_btn.clicked.connect(lambda _, task_obj=t: self.open_edit_dialog(task_obj))
            actions_layout.addWidget(edit_btn)

            del_btn = QPushButton()
            del_btn.setIcon(qta.icon("fa5s.trash-alt", color="#EF4444"))
            del_btn.setToolTip("Delete Task")
            del_btn.setFixedSize(28, 28)
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.clicked.connect(lambda _, tid=t.id, ttitle=t.title: self.delete_task(tid, ttitle))
            actions_layout.addWidget(del_btn)

            self.table.setCellWidget(row, 5, actions_widget)

    def toggle_task_completion(self, task_id: int, completed: bool):
        db = SessionLocal()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.completed = completed

                # If task belongs to a project, recalculate project progress!
                if task.project_id:
                    project = db.query(Project).filter(Project.id == task.project_id).first()
                    if project and project.tasks:
                        comp = sum(1 for item in project.tasks if item.completed)
                        project.progress = int((comp / len(project.tasks)) * 100)

                db.commit()
                self.load_tasks()
                self.data_changed.emit()
        except Exception as e:
            db.rollback()
            print(f"Error updating task: {e}")
        finally:
            db.close()

    def filter_tasks(self):
        query = self.search_box.text().lower().strip()
        status_filter = self.status_filter.currentText()
        prio_filter = self.prio_filter.currentText()
        now = datetime.now()

        filtered = self.tasks

        # Status filter
        if status_filter == "Pending Only":
            filtered = [t for t in filtered if not t.completed]
        elif status_filter == "Completed Only":
            filtered = [t for t in filtered if t.completed]
        elif status_filter == "Overdue Only":
            filtered = [t for t in filtered if not t.completed and t.deadline and t.deadline < now]

        # Priority filter
        if prio_filter != "All Priorities":
            filtered = [t for t in filtered if t.priority == prio_filter]

        # Query filter
        if query:
            filtered = [
                t for t in filtered
                if query in t.title.lower() or (t.project and query in t.project.title.lower())
            ]

        self.display_tasks(filtered)

    def open_add_dialog(self):
        dialog = TaskDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.load_tasks()
            self.data_changed.emit()

    def open_edit_dialog(self, task: Task):
        dialog = TaskDialog(task=task, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.load_tasks()
            self.data_changed.emit()

    def delete_task(self, task_id: int, title: str):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete task '{title}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            db = SessionLocal()
            try:
                t = db.query(Task).filter(Task.id == task_id).first()
                if t:
                    db.delete(t)
                    db.commit()
                    self.load_tasks()
                    self.data_changed.emit()
            except Exception as e:
                db.rollback()
                QMessageBox.critical(self, "Error", f"Failed to delete task: {e}")
            finally:
                db.close()
