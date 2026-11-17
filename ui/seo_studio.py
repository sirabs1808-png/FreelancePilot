"""
AI SEO Studio View for FreelancePilot.
Supports generating meta titles, meta descriptions, keyword clusters,
blog outlines, product descriptions, and SEO copywriting rewrites.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTextEdit, QComboBox, QFrame, QMessageBox, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import qtawesome as qta

from services.ai_service import AIWorkerThread
from database.db import SessionLocal
from database.models import Template


class SEOStudioView(QWidget):
    """
    Dedicated AI SEO & Copywriting Studio.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 32)
        layout.setSpacing(20)

        # 1. Header Banner
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("AI SEO Studio")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #F8FAFC;")
        sub = QLabel("Optimize client search ranking, generate high-CTR meta tags, and build organic content clusters.")
        sub.setFont(QFont("Segoe UI", 10))
        sub.setStyleSheet("color: #94A3B8;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        header.addStretch()

        self.generate_btn = QPushButton(" ✨ Generate SEO Assets")
        self.generate_btn.setObjectName("primaryButton")
        self.generate_btn.setCursor(Qt.PointingHandCursor)
        self.generate_btn.clicked.connect(self.on_generate)
        header.addWidget(self.generate_btn)
        layout.addLayout(header)

        # 2. Main 2-Column Body
        body = QHBoxLayout()
        body.setSpacing(20)

        # Left Column: Inputs
        form_card = QFrame()
        form_card.setStyleSheet("background: #181B22; border: 1px solid #282E3A; border-radius: 12px; padding: 16px;")
        form_layout = QVBoxLayout(form_card)
        form_layout.setSpacing(12)

        form_layout.addWidget(QLabel("<b>SEO Task Objective *</b>"))
        self.task_combo = QComboBox()
        self.task_combo.addItems([
            "Generate Meta Titles & Descriptions (~60 / ~155 chars)",
            "Keyword Research & Search Intent Clusters",
            "SEO Blog Post Outline with H1/H2/H3 Headings",
            "Full SEO-Optimized Article Draft",
            "Product Description & Feature Bullets",
            "Rewrite Existing Copy for Search Ranking"
        ])
        form_layout.addWidget(self.task_combo)

        form_layout.addWidget(QLabel("<b>Primary & Secondary Keywords *</b>"))
        self.keywords_input = QLineEdit()
        self.keywords_input.setPlaceholderText("e.g. freelance web developer, react design system, tailwind ui")
        form_layout.addWidget(self.keywords_input)

        row1 = QHBoxLayout()
        col_intent = QVBoxLayout()
        col_intent.addWidget(QLabel("Search Intent:"))
        self.intent_combo = QComboBox()
        self.intent_combo.addItems(["Commercial / Transactional (Buy/Hire)", "Informational (How-To/Learn)", "Navigational (Brand Search)"])
        col_intent.addWidget(self.intent_combo)
        row1.addLayout(col_intent)

        col_prov = QVBoxLayout()
        col_prov.addWidget(QLabel("AI Provider:"))
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["Google Gemini (Free)", "Groq LLaMA 3.3 (Free)", "Ollama (Local Offline)"])
        col_prov.addWidget(self.provider_combo)
        row1.addLayout(col_prov)
        form_layout.addLayout(row1)

        form_layout.addWidget(QLabel("<b>Page Topic / Context / Current Draft</b>"))
        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("Paste your current page copy, product details, or describe what the client sells...")
        self.content_input.setFixedHeight(110)
        form_layout.addWidget(self.content_input)

        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("color: #38BDF8; font-size: 11px; font-style: italic;")
        form_layout.addWidget(self.status_lbl)

        form_layout.addStretch()
        body.addWidget(form_card, 4)

        # Right Column: Generated SEO Assets
        output_card = QFrame()
        output_card.setStyleSheet("background: #181B22; border: 1px solid #282E3A; border-radius: 12px; padding: 16px;")
        output_layout = QVBoxLayout(output_card)
        output_layout.setSpacing(12)

        out_header = QHBoxLayout()
        out_header.addWidget(QLabel("<b>SEO Recommendations & Copy</b> (Editable)"))
        out_header.addStretch()

        copy_btn = QPushButton(" Copy All")
        copy_btn.setIcon(qta.icon("fa5s.copy", color="#94A3B8"))
        copy_btn.setCursor(Qt.PointingHandCursor)
        copy_btn.clicked.connect(self.copy_to_clipboard)
        out_header.addWidget(copy_btn)

        save_btn = QPushButton(" Save as Template")
        save_btn.setIcon(qta.icon("fa5s.bookmark", color="#94A3B8"))
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self.save_as_template)
        out_header.addWidget(save_btn)

        output_layout.addLayout(out_header)

        self.output_editor = QTextEdit()
        self.output_editor.setPlaceholderText("Optimized SEO titles, meta tags, and keyword outlines will appear here...")
        self.output_editor.setStyleSheet("""
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
        output_layout.addWidget(self.output_editor, 1)

        body.addWidget(output_card, 5)
        layout.addLayout(body, 1)

    def on_generate(self):
        task = self.task_combo.currentText()
        keywords = self.keywords_input.text().strip()
        intent = self.intent_combo.currentText()
        content = self.content_input.toPlainText().strip() or "General industry best practices"

        if not keywords:
            QMessageBox.warning(self, "Missing Keywords", "Please specify at least one target keyword.")
            return

        idx = self.provider_combo.currentIndex()
        provider_map = {0: "gemini", 1: "groq", 2: "ollama"}
        provider = provider_map.get(idx, "gemini")

        prompt = f"""
Act as a senior technical SEO director and search copywriter.
Task: {task}
Target Keywords: {keywords}
Search Intent: {intent}

Context / Draft Input:
{content}

Deliver high-impact, professional results formatted with clean markdown:
- If Meta Tags: Provide 3 distinct Title Tag options (under 60 chars) and 3 Meta Description options (under 155 chars) with character counts.
- If Keywords: Provide primary keywords, secondary long-tail queries, and searcher questions.
- If Outlines/Articles: Provide clear H1, H2, H3 hierarchy optimized for search intent and featured snippets.
"""

        system_instruction = "You are an elite Google SEO specialist and high-conversion search copywriter."

        self.generate_btn.setEnabled(False)
        self.status_lbl.setText(f"✨ Generating SEO assets with {provider.capitalize()}...")

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
        self.output_editor.setPlainText(result["text"])

    def on_generation_failed(self, error_message: str):
        self.generate_btn.setEnabled(True)
        self.status_lbl.setText("")
        QMessageBox.critical(self, "SEO Generation Error", f"Failed to generate SEO assets:\n\n{error_message}\n\nPlease check your API keys in Settings.")

    def copy_to_clipboard(self):
        text = self.output_editor.toPlainText().strip()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copied", "SEO copy copied to clipboard!")

    def save_as_template(self):
        text = self.output_editor.toPlainText().strip()
        task = self.task_combo.currentText().split("(")[0].strip()
        if not text:
            QMessageBox.warning(self, "Empty Output", "Generate SEO content first before saving.")
            return

        db = SessionLocal()
        try:
            tmpl = Template(
                title=f"SEO: {task} - {self.keywords_input.text()[:25]}",
                category="SEO",
                content=text
            )
            db.add(tmpl)
            db.commit()
            QMessageBox.information(self, "Saved", "SEO asset saved to your Templates Library!")
        finally:
            db.close()
