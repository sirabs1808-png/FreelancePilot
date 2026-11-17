"""
Templates Library View for FreelancePilot.
Supports managing, creating, editing, and copying reusable proposals,
business emails, quotations, and SEO content templates.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QComboBox, QFrame,
    QMessageBox, QDialog, QApplication
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import qtawesome as qta

from database.db import SessionLocal
from database.models import Template
from components.dialogs import TemplateDialog
from components.cards import StatCard, StatusBadge


class TemplatesView(QWidget):
    """
    Reusable Document Templates Library Screen.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.templates = []
        self.init_ui()
        self.seed_default_templates()
        self.load_templates()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 32)
        layout.setSpacing(20)

        # 1. Header Banner
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Templates Library")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #F8FAFC;")
        sub = QLabel("Reusable boilerplate templates for client proposals, payment reminders, scope changes, and SEO.")
        sub.setFont(QFont("Segoe UI", 10))
        sub.setStyleSheet("color: #94A3B8;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        header.addStretch()

        self.create_btn = QPushButton(" + New Template")
        self.create_btn.setObjectName("primaryButton")
        self.create_btn.setCursor(Qt.PointingHandCursor)
        self.create_btn.clicked.connect(self.open_create_dialog)
        header.addWidget(self.create_btn)
        layout.addLayout(header)

        # 2. Stats Strip
        self.stats_row = QHBoxLayout()
        self.stats_row.setSpacing(14)

        self.stat_total = StatCard("TOTAL TEMPLATES", "0", "fa5s.folder-open", "Available presets", True, "#3B82F6")
        self.stat_proposals = StatCard("PROPOSALS", "0", "fa5s.file-contract", "Ready to send", True, "#8B5CF6")
        self.stat_emails = StatCard("EMAILS & OUTREACH", "0", "fa5s.envelope-open-text", "Client communications", True, "#10B981")

        self.stats_row.addWidget(self.stat_total)
        self.stats_row.addWidget(self.stat_proposals)
        self.stats_row.addWidget(self.stat_emails)
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
        self.search_box.setPlaceholderText("Search templates by title or content...")
        self.search_box.setStyleSheet("background: transparent; border: none; color: #F8FAFC;")
        self.search_box.textChanged.connect(self.filter_templates)
        s_layout.addWidget(self.search_box)
        action_bar.addWidget(search_frame, 1)

        cat_lbl = QLabel("Category:")
        cat_lbl.setStyleSheet("color: #94A3B8; font-weight: 500;")
        action_bar.addWidget(cat_lbl)

        self.cat_filter = QComboBox()
        self.cat_filter.addItems(["All Categories", "Proposals", "Emails & Outreach", "Quotations", "SEO", "Invoices", "General"])
        self.cat_filter.setFixedWidth(160)
        self.cat_filter.currentTextChanged.connect(lambda _: self.filter_templates())
        action_bar.addWidget(self.cat_filter)

        refresh_btn = QPushButton(" Refresh")
        refresh_btn.setIcon(qta.icon("fa5s.sync", color="#94A3B8"))
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.load_templates)
        action_bar.addWidget(refresh_btn)

        layout.addLayout(action_bar)

        # 4. Templates Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Title", "Category", "Content Preview", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table, 1)

    def seed_default_templates(self):
        db = SessionLocal()
        try:
            if db.query(Template).count() == 0:
                defaults = [
                    Template(
                        title="Polite Milestone Payment Reminder",
                        category="Emails & Outreach",
                        content="Hi [Client Name],\n\nHope you're having a productive week! Just sending a quick note regarding Invoice #[Invoice Number] for [Project Title], which reached its due date on [Due Date].\n\nCould you kindly confirm when this will be processed? Please let me know if you need any updated billing details or documentation.\n\nThank you,\n[Your Name]"
                    ),
                    Template(
                        title="Scope Creep & Change Order Notice",
                        category="Emails & Outreach",
                        content="Hi [Client Name],\n\nThanks for sharing the additional feature ideas! I reviewed the request for [New Feature]. This falls outside our original milestone scope agreed in the proposal.\n\nTo ensure we maintain delivery quality without delaying our target launch date of [Launch Date], I'd be happy to prepare a separate change order quote ($[Price], [Time Estimate]).\n\nLet me know how you'd like to proceed!\n\nBest regards,\n[Your Name]"
                    ),
                    Template(
                        title="High-Converting Cold Client Outreach",
                        category="Emails & Outreach",
                        content="Hi [Prospect Name],\n\nI came across [Company Name] and noticed [Specific Observation, e.g., mobile viewport performance or checkout flow friction].\n\nI help modern brands like yours improve [Metric, e.g. conversion rate / load speed] by rebuilding frontend experiences with React and clean design systems.\n\nI put together 3 quick suggestions for your team—would you be open to a 10-minute async loom or call this Thursday?\n\nBest,\n[Your Name]"
                    ),
                    Template(
                        title="Web & Mobile Development Proposal Boilerplate",
                        category="Proposals",
                        content="# Executive Overview\nThis engagement outlines the design system architecture, responsive frontend, and API integrations for [Client Name].\n\n## Core Deliverables\n- Production React/Next.js application\n- WCAG AAA accessibility compliance\n- Automated test coverage & continuous integration\n- 30-day post-launch bug warranty\n\n## Commercial Terms\n- Total Investment: $[Budget]\n- Milestone 1: 50% upfront deposit\n- Milestone 2: 50% upon final staging approval and handover"
                    ),
                    Template(
                        title="SEO Technical Audit & Strategy Brief",
                        category="SEO",
                        content="# Technical SEO & Content Optimization Audit\nClient: [Client Name]\n\n## 1. On-Page Structure\n- Implement canonical tags and structured JSON-LD schema\n- Optimize Title Tags under 60 characters and Meta Descriptions under 155 characters\n\n## 2. Core Web Vitals\n- Image optimization (WebP/AVIF format)\n- Cumulative Layout Shift (CLS) reduction below 0.1\n- Largest Contentful Paint (LCP) under 2.5s"
                    )
                ]
                db.add_all(defaults)
                db.commit()
        finally:
            db.close()

    def load_templates(self):
        db = SessionLocal()
        try:
            self.templates = db.query(Template).all()
            self.display_templates(self.templates)

            # Update stats
            total = len(self.templates)
            props = sum(1 for t in self.templates if t.category == "Proposals")
            emails = sum(1 for t in self.templates if t.category == "Emails & Outreach")

            self.stat_total.update_value(str(total))
            self.stat_proposals.update_value(str(props))
            self.stat_emails.update_value(str(emails))
        finally:
            db.close()

    def display_templates(self, templates):
        self.table.setRowCount(len(templates))
        for row, t in enumerate(templates):
            self.table.setItem(row, 0, QTableWidgetItem(t.title))

            # Category
            cat_item = QTableWidgetItem(t.category)
            self.table.setItem(row, 1, cat_item)

            # Preview (single line snippet)
            clean_snippet = t.content.replace("\n", " ").strip()[:80] + ("..." if len(t.content) > 80 else "")
            self.table.setItem(row, 2, QTableWidgetItem(clean_snippet))

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(6, 2, 6, 2)
            actions_layout.setSpacing(6)

            copy_btn = QPushButton()
            copy_btn.setIcon(qta.icon("fa5s.copy", color="#38BDF8"))
            copy_btn.setToolTip("Copy Template to Clipboard")
            copy_btn.setFixedSize(28, 28)
            copy_btn.setCursor(Qt.PointingHandCursor)
            copy_btn.clicked.connect(lambda _, text=t.content: self.copy_template(text))
            actions_layout.addWidget(copy_btn)

            edit_btn = QPushButton()
            edit_btn.setIcon(qta.icon("fa5s.edit", color="#F59E0B"))
            edit_btn.setToolTip("Edit Template")
            edit_btn.setFixedSize(28, 28)
            edit_btn.setCursor(Qt.PointingHandCursor)
            edit_btn.clicked.connect(lambda _, tmpl_obj=t: self.open_edit_dialog(tmpl_obj))
            actions_layout.addWidget(edit_btn)

            del_btn = QPushButton()
            del_btn.setIcon(qta.icon("fa5s.trash-alt", color="#EF4444"))
            del_btn.setToolTip("Delete Template")
            del_btn.setFixedSize(28, 28)
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.clicked.connect(lambda _, tid=t.id, title=t.title: self.delete_template(tid, title))
            actions_layout.addWidget(del_btn)

            self.table.setCellWidget(row, 3, actions_widget)

    def filter_templates(self):
        query = self.search_box.text().lower().strip()
        cat = self.cat_filter.currentText()

        filtered = self.templates
        if cat != "All Categories":
            filtered = [t for t in filtered if t.category == cat]

        if query:
            filtered = [
                t for t in filtered
                if query in t.title.lower() or query in t.content.lower() or query in t.category.lower()
            ]

        self.display_templates(filtered)

    def copy_template(self, text: str):
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Copied", "Template content copied to clipboard!")

    def open_create_dialog(self):
        diag = TemplateDialog(parent=self)
        if diag.exec() == QDialog.Accepted:
            self.load_templates()

    def open_edit_dialog(self, template: Template):
        diag = TemplateDialog(template=template, parent=self)
        if diag.exec() == QDialog.Accepted:
            self.load_templates()

    def delete_template(self, template_id: int, title: str):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete template '{title}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            db = SessionLocal()
            try:
                t = db.query(Template).filter(Template.id == template_id).first()
                if t:
                    db.delete(t)
                    db.commit()
                    self.load_templates()
            except Exception as e:
                db.rollback()
                QMessageBox.critical(self, "Error", f"Failed to delete template: {e}")
            finally:
                db.close()
