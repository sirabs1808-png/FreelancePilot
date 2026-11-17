"""
AI Assistant View for FreelancePilot.
Integrates live free-tier AI generation (Google Gemini, Groq, Ollama)
with asynchronous background worker threads (QThread), tone selection,
copying, and template saving.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QTextEdit, QScrollArea, QFrame, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import qtawesome as qta

from services.ai_service import AIProviderManager, AIWorkerThread
from database.db import SessionLocal
from database.models import Template


class AIAssistantView(QWidget):
    """
    Interactive AI Assistant interface for writing emails, proposals, SEO, and summaries.
    """
    navigate_to = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 32)
        layout.setSpacing(18)

        # 1. Header with Provider Selector
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("AI Business Assistant")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #F8FAFC;")
        sub = QLabel("Powered by free AI models: Google Gemini, Groq (LLaMA 3.3), and local Ollama.")
        sub.setFont(QFont("Segoe UI", 10))
        sub.setStyleSheet("color: #94A3B8;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        header.addStretch()

        prov_lbl = QLabel("Provider:")
        prov_lbl.setStyleSheet("color: #94A3B8; font-weight: 500;")
        header.addWidget(prov_lbl)

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["Google Gemini (Free)", "Groq LLaMA 3.3 (Free)", "Ollama (Local Offline)"])
        self.provider_combo.setFixedWidth(210)
        header.addWidget(self.provider_combo)

        clear_btn = QPushButton(" Clear Chat")
        clear_btn.setIcon(qta.icon("fa5s.trash-alt", color="#94A3B8"))
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #1D2128;
                border: 1px solid #282E3A;
                border-radius: 8px;
                padding: 6px 12px;
                color: #94A3B8;
            }
            QPushButton:hover {
                background: #EF444422;
                border-color: #EF4444;
                color: #EF4444;
            }
        """)
        clear_btn.clicked.connect(self.clear_chat)
        header.addWidget(clear_btn)
        layout.addLayout(header)

        # 2. Prompt Quick Suggestion Chips
        chips_layout = QHBoxLayout()
        chips_layout.setSpacing(10)
        chips = [
            ("fa5s.envelope", "Draft Client Cold Outreach"),
            ("fa5s.file-invoice", "Polite Payment Reminder"),
            ("fa5s.handshake", "Scope Revision Agreement"),
            ("fa5s.bullhorn", "Write Service Description"),
        ]
        for icon, text in chips:
            chip_btn = QPushButton(f" {text}")
            chip_btn.setIcon(qta.icon(icon, color="#3B82F6"))
            chip_btn.setCursor(Qt.PointingHandCursor)
            chip_btn.setStyleSheet("""
                QPushButton {
                    background: #181B22;
                    border: 1px solid #282E3A;
                    border-radius: 20px;
                    padding: 6px 14px;
                    color: #94A3B8;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background: #2563EB20;
                    border-color: #2563EB;
                    color: #38BDF8;
                }
            """)
            chip_btn.clicked.connect(lambda _, t=text: self.set_prompt_suggestion(t))
            chips_layout.addWidget(chip_btn)

        chips_layout.addStretch()
        layout.addLayout(chips_layout)

        # 3. Chat Stream Area (Scrollable)
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setFrameShape(QFrame.NoFrame)
        self.chat_scroll.setStyleSheet("background: #16191E; border: 1px solid #282E3A; border-radius: 12px;")

        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("background: transparent;")
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(20, 20, 20, 20)
        self.chat_layout.setSpacing(16)

        # Welcome initial AI message
        self._add_ai_message(
            "Hello Alex! I am your FreelancePilot AI copilot. How can I assist your business today?\n\n"
            "• Draft high-converting freelance proposals & estimates\n"
            "• Write persuasive client follow-up emails\n"
            "• Generate SEO articles, keywords, and blog outlines\n"
            "• Review contracts and rewrite client communication\n\n"
            "Tip: Ensure you have added your free Gemini or Groq key in Settings."
        )

        self.chat_scroll.setWidget(self.chat_container)
        layout.addWidget(self.chat_scroll, 1)

        # 4. Input Box + Controls
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background: #181B22;
                border: 1px solid #282E3A;
                border-radius: 12px;
                padding: 8px;
            }
        """)
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(8, 8, 8, 8)
        input_layout.setSpacing(8)

        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Ask the AI anything (e.g., 'Write a follow-up email to Marcus about milestone 2 payment')...")
        self.prompt_input.setFixedHeight(75)
        self.prompt_input.setStyleSheet("background: transparent; border: none; color: #F8FAFC; font-size: 13px;")
        input_layout.addWidget(self.prompt_input)

        bottom_bar = QHBoxLayout()
        tone_lbl = QLabel("Tone:")
        tone_lbl.setStyleSheet("color: #64748B; font-size: 11px;")
        bottom_bar.addWidget(tone_lbl)

        self.tone_combo = QComboBox()
        self.tone_combo.addItems(["Professional", "Persuasive", "Friendly", "Direct & Concise", "Formal"])
        self.tone_combo.setFixedWidth(140)
        bottom_bar.addWidget(self.tone_combo)

        # Status text while generating
        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("color: #38BDF8; font-size: 12px; font-style: italic;")
        bottom_bar.addWidget(self.status_lbl)

        bottom_bar.addStretch()

        self.send_btn = QPushButton(" Send Request")
        self.send_btn.setIcon(qta.icon("fa5s.paper-plane", color="#FFFFFF"))
        self.send_btn.setObjectName("primaryButton")
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.clicked.connect(self.on_send)
        bottom_bar.addWidget(self.send_btn)

        input_layout.addLayout(bottom_bar)
        layout.addWidget(input_frame)

    def set_prompt_suggestion(self, text: str):
        self.prompt_input.setText(f"Please help me write a {text.lower()} for a client engagement.")

    def clear_chat(self):
        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._add_ai_message("Conversation cleared. How can I assist you?")

    def on_send(self):
        query = self.prompt_input.toPlainText().strip()
        if not query:
            return

        # Determine chosen provider
        idx = self.provider_combo.currentIndex()
        provider_map = {0: "gemini", 1: "groq", 2: "ollama"}
        provider = provider_map.get(idx, "gemini")

        tone = self.tone_combo.currentText()
        system_prompt = (
            f"You are FreelancePilot AI, an elite business copilot for freelance software engineers, "
            f"designers, and agencies. Write in a {tone.lower()} tone. Provide actionable, high-quality, "
            f"ready-to-send content."
        )

        self._add_user_message(query)
        self.prompt_input.clear()

        # Update UI state for background generation
        self.send_btn.setEnabled(False)
        self.status_lbl.setText(f"✨ Generating with {provider.capitalize()}...")

        # Launch QThread background worker
        self.worker = AIWorkerThread(
            prompt=query,
            provider=provider,
            system_instruction=system_prompt,
            parent=self
        )
        self.worker.finished_result.connect(self.on_generation_finished)
        self.worker.failed_error.connect(self.on_generation_failed)
        self.worker.start()

    def on_generation_finished(self, result: dict):
        self.send_btn.setEnabled(True)
        self.status_lbl.setText("")

        text = result["text"]
        provider_used = result.get("provider_used", "AI")
        fallback_used = result.get("fallback_used", False)

        tag = f" ({provider_used.capitalize()}" + (" - Fallback)" if fallback_used else ")")
        self._add_ai_message(text, tag=tag)

        # Scroll to bottom
        QApplication.processEvents()
        self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        )

    def on_generation_failed(self, error_message: str):
        self.send_btn.setEnabled(True)
        self.status_lbl.setText("")

        self._add_ai_message(
            f"⚠️ **Generation Failed:**\n\n{error_message}\n\n"
            f"💡 **Tip:** Go to **Settings** to check your API key or configure a fallback provider.",
            tag=" (Error)"
        )

    def _add_user_message(self, text: str):
        msg = QFrame()
        msg.setStyleSheet("""
            QFrame {
                background: #2563EB24;
                border: 1px solid #2563EB55;
                border-radius: 10px;
                padding: 12px;
            }
        """)
        l = QVBoxLayout(msg)
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("color: #F8FAFC; border: none; background: transparent;")
        l.addWidget(lbl)
        self.chat_layout.addWidget(msg)

    def _add_ai_message(self, text: str, tag: str = ""):
        msg = QFrame()
        msg.setStyleSheet("""
            QFrame {
                background: #1D2128;
                border: 1px solid #282E3A;
                border-radius: 10px;
                padding: 14px;
            }
        """)
        l = QVBoxLayout(msg)

        head = QHBoxLayout()
        copilot_title = QLabel(f"<b>FreelancePilot Copilot</b><font color='#94A3B8'>{tag}</font>")
        copilot_title.setStyleSheet("border: none; background: transparent; font-size: 11px;")
        head.addWidget(copilot_title)
        head.addStretch()
        l.addLayout(head)

        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lbl.setStyleSheet("color: #E2E8F0; border: none; background: transparent; line-height: 1.4;")
        l.addWidget(lbl)

        # Actions
        actions = QHBoxLayout()
        copy_btn = QPushButton(" Copy")
        copy_btn.setIcon(qta.icon("fa5s.copy", color="#94A3B8"))
        copy_btn.setCursor(Qt.PointingHandCursor)
        copy_btn.setStyleSheet("background: transparent; border: none; color: #94A3B8; font-size: 11px;")
        copy_btn.clicked.connect(lambda: self._copy_to_clipboard(text))
        actions.addWidget(copy_btn)

        save_btn = QPushButton(" Save to Templates")
        save_btn.setIcon(qta.icon("fa5s.bookmark", color="#94A3B8"))
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet("background: transparent; border: none; color: #94A3B8; font-size: 11px;")
        save_btn.clicked.connect(lambda: self._save_template(text))
        actions.addWidget(save_btn)
        actions.addStretch()

        l.addLayout(actions)
        self.chat_layout.addWidget(msg)

    def _copy_to_clipboard(self, text: str):
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Copied", "Content copied to clipboard!")

    def _save_template(self, text: str):
        db = SessionLocal()
        try:
            tmpl = Template(
                title=f"AI Draft ({text[:30].strip()}...)",
                category="AI Generated",
                content=text
            )
            db.add(tmpl)
            db.commit()
            QMessageBox.information(self, "Saved", "Saved to your Templates Library!")
        finally:
            db.close()
