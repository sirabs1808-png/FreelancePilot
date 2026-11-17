"""
AI Proposal Generator View for FreelancePilot.
Generates comprehensive client proposals with scope, milestones, pricing, and timelines,
with one-click PDF export, clipboard copying, and template saving.
"""

from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTextEdit, QComboBox, QFrame, QMessageBox, QApplication, QFileDialog
)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QFont, QDesktopServices
import qtawesome as qta

from database.db import SessionLocal
from database.models import Client, Template
from services.ai_service import AIWorkerThread
from services.pdf_service import PDFService


class ProposalGeneratorView(QWidget):
    """
    Dedicated AI Proposal Builder Screen.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.init_ui()
        self.load_clients()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 32)
        layout.setSpacing(20)

        # 1. Header
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("AI Proposal Generator")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #F8FAFC;")
        sub = QLabel("Generate high-converting freelance proposals with deliverables, timelines, pricing, and terms.")
        sub.setFont(QFont("Segoe UI", 10))
        sub.setStyleSheet("color: #94A3B8;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        header.addStretch()

        self.generate_btn = QPushButton(" ✨ Generate Proposal")
        self.generate_btn.setObjectName("primaryButton")
        self.generate_btn.setCursor(Qt.PointingHandCursor)
        self.generate_btn.clicked.connect(self.on_generate)
        header.addWidget(self.generate_btn)
        layout.addLayout(header)

        # 2. Main 2-Column Body Layout
        body = QHBoxLayout()
        body.setSpacing(20)

        # Left Column: Project Parameters
        form_card = QFrame()
        form_card.setStyleSheet("background: #181B22; border: 1px solid #282E3A; border-radius: 12px; padding: 16px;")
        form_layout = QVBoxLayout(form_card)
        form_layout.setSpacing(10)

        # Client selection
        form_layout.addWidget(QLabel("<b>Client Name / Company *</b>"))
        self.client_combo = QComboBox()
        self.client_combo.setEditable(True)
        form_layout.addWidget(self.client_combo)

        # Project title
        form_layout.addWidget(QLabel("<b>Project Title *</b>"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g. Next.js SaaS Platform & Stripe Integration")
        form_layout.addWidget(self.title_input)

        # Industry & Tone row
        row1 = QHBoxLayout()
        col_ind = QVBoxLayout()
        col_ind.addWidget(QLabel("Industry / Vertical:"))
        self.industry_combo = QComboBox()
        self.industry_combo.addItems(["Technology & SaaS", "E-Commerce", "Digital Agency", "Healthcare & Wellness", "Finance & Real Estate", "Creative / Entertainment"])
        col_ind.addWidget(self.industry_combo)
        row1.addLayout(col_ind)

        col_tone = QVBoxLayout()
        col_tone.addWidget(QLabel("Proposal Tone:"))
        self.tone_combo = QComboBox()
        self.tone_combo.addItems(["Persuasive & High-Converting", "Executive & Formal", "Modern & Consultative", "Concise & Direct"])
        col_tone.addWidget(self.tone_combo)
        row1.addLayout(col_tone)
        form_layout.addLayout(row1)

        # Services & Scope
        form_layout.addWidget(QLabel("<b>Required Deliverables & Scope *</b>"))
        self.services_input = QTextEdit()
        self.services_input.setPlaceholderText("e.g. UI/UX design tokens in Figma, responsive frontend in React, REST API integration, automated testing, 30 days post-launch warranty...")
        self.services_input.setFixedHeight(85)
        form_layout.addWidget(self.services_input)

        # Budget & Timeline row
        row2 = QHBoxLayout()
        col_budget = QVBoxLayout()
        col_budget.addWidget(QLabel("Estimated Budget ($):"))
        self.budget_input = QLineEdit()
        self.budget_input.setPlaceholderText("e.g. 6,500")
        col_budget.addWidget(self.budget_input)
        row2.addLayout(col_budget)

        col_time = QVBoxLayout()
        col_time.addWidget(QLabel("Estimated Timeline:"))
        self.timeline_input = QLineEdit()
        self.timeline_input.setPlaceholderText("e.g. 4 weeks with weekly demo sprints")
        col_time.addWidget(self.timeline_input)
        row2.addLayout(col_time)
        form_layout.addLayout(row2)

        # AI Provider selector
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("AI Engine:"))
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["Google Gemini (Free)", "Groq LLaMA 3.3 (Free)", "Ollama (Local Offline)"])
        row3.addWidget(self.provider_combo)
        form_layout.addLayout(row3)

        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("color: #38BDF8; font-size: 11px; font-style: italic;")
        form_layout.addWidget(self.status_lbl)

        form_layout.addStretch()
        body.addWidget(form_card, 4)

        # Right Column: Generated Proposal Editor & Actions
        output_card = QFrame()
        output_card.setStyleSheet("background: #181B22; border: 1px solid #282E3A; border-radius: 12px; padding: 16px;")
        output_layout = QVBoxLayout(output_card)
        output_layout.setSpacing(12)

        out_header = QHBoxLayout()
        out_header.addWidget(QLabel("<b>Proposal Document</b> (Editable)"))
        out_header.addStretch()

        copy_btn = QPushButton(" Copy")
        copy_btn.setIcon(qta.icon("fa5s.copy", color="#94A3B8"))
        copy_btn.setCursor(Qt.PointingHandCursor)
        copy_btn.clicked.connect(self.copy_to_clipboard)
        out_header.addWidget(copy_btn)

        save_tmpl_btn = QPushButton(" Save as Template")
        save_tmpl_btn.setIcon(qta.icon("fa5s.bookmark", color="#94A3B8"))
        save_tmpl_btn.setCursor(Qt.PointingHandCursor)
        save_tmpl_btn.clicked.connect(self.save_as_template)
        out_header.addWidget(save_tmpl_btn)

        self.pdf_btn = QPushButton(" Export PDF")
        self.pdf_btn.setIcon(qta.icon("fa5s.file-pdf", color="#EF4444"))
        self.pdf_btn.setCursor(Qt.PointingHandCursor)
        self.pdf_btn.clicked.connect(self.export_pdf)
        out_header.addWidget(self.pdf_btn)

        output_layout.addLayout(out_header)

        # Proposal Editor Text Area
        self.proposal_editor = QTextEdit()
        self.proposal_editor.setPlaceholderText("Click 'Generate Proposal' on the left to write an executive freelance proposal...")
        self.proposal_editor.setStyleSheet("""
            QTextEdit {
                background: #16191E;
                border: 1px solid #282E3A;
                border-radius: 8px;
                color: #F8FAFC;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                line-height: 1.5;
                padding: 12px;
            }
        """)
        output_layout.addWidget(self.proposal_editor, 1)

        body.addWidget(output_card, 5)
        layout.addLayout(body, 1)

    def load_clients(self):
        db = SessionLocal()
        try:
            clients = db.query(Client).all()
            self.client_combo.clear()
            self.client_combo.addItem("Select existing client or type custom name...")
            for c in clients:
                label = f"{c.name} ({c.company})" if c.company else c.name
                self.client_combo.addItem(label)
        finally:
            db.close()

    def on_generate(self):
        client = self.client_combo.currentText().strip()
        if client.startswith("Select existing"):
            client = "Valued Client"

        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Missing Title", "Please enter a project title.")
            return

        scope = self.services_input.toPlainText().strip()
        if not scope:
            QMessageBox.warning(self, "Missing Scope", "Please specify required deliverables or services.")
            return

        budget = self.budget_input.text().strip() or "To be agreed based on milestones"
        timeline = self.timeline_input.text().strip() or "Standard milestone-based schedule"
        industry = self.industry_combo.currentText()
        tone = self.tone_combo.currentText()

        idx = self.provider_combo.currentIndex()
        provider_map = {0: "gemini", 1: "groq", 2: "ollama"}
        provider = provider_map.get(idx, "gemini")

        prompt = f"""
Write a comprehensive, winning freelance business proposal for the following engagement:

Client: {client}
Project Title: {title}
Industry: {industry}
Tone: {tone}
Scope & Deliverables:
{scope}

Budget: ${budget}
Timeline: {timeline}

Structure the proposal with clean markdown headings:
1. Executive Summary & Objective
2. Detailed Scope of Deliverables
3. Project Milestones & Delivery Schedule
4. Investment & Budget Summary
5. Why Choose Our Studio
6. Next Steps & Acceptance

Write with persuasive clarity, highlighting value, modern delivery standards, and commercial reliability.
"""

        system_instruction = "You are a world-class freelance proposal writer and agency strategist. Create ready-to-sign proposals."

        self.generate_btn.setEnabled(False)
        self.status_lbl.setText(f"✨ Generating proposal with {provider.capitalize()}...")

        self.worker = AIWorkerThread(
            prompt=prompt,
            provider=provider,
            system_instruction=system_instruction,
            parent=self
        )
        self.worker.finished_result.connect(self.on_generation_finished)
        self.worker.failed_error.connect(self.on_generation_failed)
        self.worker.start()

    def on_generation_finished(self, result: dict):
        self.generate_btn.setEnabled(True)
        self.status_lbl.setText("")
        self.proposal_editor.setPlainText(result["text"])

    def on_generation_failed(self, error_message: str):
        self.generate_btn.setEnabled(True)
        self.status_lbl.setText("")
        QMessageBox.critical(self, "Generation Error", f"Failed to generate proposal:\n\n{error_message}\n\nPlease check your API keys in Settings.")

    def copy_to_clipboard(self):
        text = self.proposal_editor.toPlainText().strip()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copied", "Proposal copied to clipboard!")

    def save_as_template(self):
        text = self.proposal_editor.toPlainText().strip()
        title = self.title_input.text().strip() or "Custom Client Proposal"
        if not text:
            QMessageBox.warning(self, "Empty Proposal", "Generate or write a proposal first before saving.")
            return

        db = SessionLocal()
        try:
            tmpl = Template(
                title=f"Proposal: {title}",
                category="Proposals",
                content=text
            )
            db.add(tmpl)
            db.commit()
            QMessageBox.information(self, "Saved", "Proposal saved to your Templates Library!")
        finally:
            db.close()

    def export_pdf(self):
        content = self.proposal_editor.toPlainText().strip()
        title = self.title_input.text().strip() or "Client Proposal"
        client = self.client_combo.currentText().strip()

        if not content:
            QMessageBox.warning(self, "Empty Proposal", "Please generate or write a proposal before exporting to PDF.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Proposal PDF",
            f"Proposal_{title.replace(' ', '_')}.pdf",
            "PDF Files (*.pdf)"
        )
        if file_path:
            try:
                PDFService.generate_proposal_pdf(
                    proposal_title=title,
                    client_name=client,
                    content=content,
                    output_path=file_path
                )
                reply = QMessageBox.question(
                    self,
                    "PDF Generated",
                    f"Proposal successfully exported to:\n{file_path}\n\nWould you like to open it now?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                if reply == QMessageBox.Yes:
                    QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
            except Exception as e:
                QMessageBox.critical(self, "PDF Export Error", f"Failed to generate PDF: {e}")
