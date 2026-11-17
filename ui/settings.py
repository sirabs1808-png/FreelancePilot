"""
Settings View for FreelancePilot.
Allows user configuration of appearance, AI API keys, local Ollama,
business profile details, currency, and database backups.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QComboBox, QFrame, QScrollArea, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import qtawesome as qta

from database.db import SessionLocal
from database.models import Setting
from services.ai_service import AIProviderManager
from services.gemini_service import GeminiService
from services.groq_service import GroqService
from services.ollama_service import OllamaService


class SettingsView(QWidget):
    """
    Application Settings Screen.
    """
    theme_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 28, 32, 32)
        layout.setSpacing(24)

        # Header
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Settings & Preferences")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #F8FAFC;")
        sub = QLabel("Configure free AI provider credentials, visual themes, business branding, and local backups.")
        sub.setFont(QFont("Segoe UI", 10))
        sub.setStyleSheet("color: #94A3B8;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        header.addStretch()

        save_btn = QPushButton(" Save All Settings")
        save_btn.setObjectName("primaryButton")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self.save_settings)
        header.addWidget(save_btn)
        layout.addLayout(header)

        # 1. Appearance Section
        app_card = self._create_card("Appearance & Display", "Choose visual style and presentation options.")
        app_layout = QVBoxLayout(app_card)
        app_layout.setSpacing(12)

        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Interface Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark (Slate Charcoal & Electric Blue)", "Light (Clean Paper)"])
        self.theme_combo.currentIndexChanged.connect(self._on_theme_select)
        theme_row.addWidget(self.theme_combo)
        theme_row.addStretch()
        app_layout.addLayout(theme_row)
        layout.addWidget(app_card)

        # 2. AI Providers Configuration (Gemini, Groq, Ollama)
        ai_card = self._create_card("Free AI Providers Configuration", "Manage free-tier AI keys, test connections, and configure fallbacks.")
        ai_layout = QVBoxLayout(ai_card)
        ai_layout.setSpacing(14)

        # Routing dropdowns: Default & Fallback
        route_row = QHBoxLayout()
        route_row.setSpacing(16)

        col_def = QVBoxLayout()
        col_def.addWidget(QLabel("<b>Primary AI Provider:</b>"))
        self.primary_ai_combo = QComboBox()
        self.primary_ai_combo.addItems(["Google Gemini (Free)", "Groq Developer (Free)", "Ollama (Local Offline)"])
        col_def.addWidget(self.primary_ai_combo)
        route_row.addLayout(col_def)

        col_fall = QVBoxLayout()
        col_fall.addWidget(QLabel("<b>Fallback Provider (if rate-limited):</b>"))
        self.fallback_ai_combo = QComboBox()
        self.fallback_ai_combo.addItems(["Groq Developer (Free)", "Google Gemini (Free)", "Ollama (Local Offline)", "None"])
        col_fall.addWidget(self.fallback_ai_combo)
        route_row.addLayout(col_fall)

        ai_layout.addLayout(route_row)

        # Google Gemini
        ai_layout.addWidget(QLabel("<b>Google Gemini API Key</b> (Free Tier at aistudio.google.com)"))
        g_row = QHBoxLayout()
        self.gemini_key = QLineEdit()
        self.gemini_key.setEchoMode(QLineEdit.Password)
        self.gemini_key.setPlaceholderText("Enter your Google AI Studio API key...")
        g_row.addWidget(self.gemini_key, 4)

        self.test_g_btn = QPushButton("Test Gemini")
        self.test_g_btn.setCursor(Qt.PointingHandCursor)
        self.test_g_btn.clicked.connect(self.test_gemini)
        g_row.addWidget(self.test_g_btn, 1)
        ai_layout.addLayout(g_row)

        # Groq
        ai_layout.addWidget(QLabel("<b>Groq Developer API Key</b> (Free Tier at console.groq.com)"))
        groq_row = QHBoxLayout()
        self.groq_key = QLineEdit()
        self.groq_key.setEchoMode(QLineEdit.Password)
        self.groq_key.setPlaceholderText("Enter your Groq API key (starts with gsk_)...")
        groq_row.addWidget(self.groq_key, 4)

        self.test_gr_btn = QPushButton("Test Groq")
        self.test_gr_btn.setCursor(Qt.PointingHandCursor)
        self.test_gr_btn.clicked.connect(self.test_groq)
        groq_row.addWidget(self.test_gr_btn, 1)
        ai_layout.addLayout(groq_row)

        # Ollama Local
        ai_layout.addWidget(QLabel("<b>Ollama Local Instance</b> (100% Private, offline)"))
        ollama_row = QHBoxLayout()
        self.ollama_url = QLineEdit()
        self.ollama_url.setText("http://localhost:11434")
        self.ollama_url.setPlaceholderText("http://localhost:11434")
        ollama_row.addWidget(self.ollama_url, 4)

        self.test_ol_btn = QPushButton("Test Ollama")
        self.test_ol_btn.setCursor(Qt.PointingHandCursor)
        self.test_ol_btn.clicked.connect(self.test_ollama)
        ollama_row.addWidget(self.test_ol_btn, 1)
        ai_layout.addLayout(ollama_row)

        layout.addWidget(ai_card)

        # 3. Business Profile & Invoicing Details
        biz_card = self._create_card("Business Profile & Invoices", "Information printed on exported client invoices and contracts.")
        biz_layout = QVBoxLayout(biz_card)
        biz_layout.setSpacing(12)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Business / Studio Name:"))
        self.biz_name = QLineEdit()
        name_row.addWidget(self.biz_name)
        biz_layout.addLayout(name_row)

        email_row = QHBoxLayout()
        email_row.addWidget(QLabel("Business Email:"))
        self.biz_email = QLineEdit()
        email_row.addWidget(self.biz_email)
        biz_layout.addLayout(email_row)

        phone_row = QHBoxLayout()
        phone_row.addWidget(QLabel("Business Phone:"))
        self.biz_phone = QLineEdit()
        phone_row.addWidget(self.biz_phone)
        biz_layout.addLayout(phone_row)

        curr_row = QHBoxLayout()
        curr_row.addWidget(QLabel("Default Currency:"))
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["USD ($)", "EUR (€)", "GBP (£)", "CAD ($)", "AUD ($)"])
        curr_row.addWidget(self.currency_combo)
        curr_row.addStretch()
        biz_layout.addLayout(curr_row)

        layout.addWidget(biz_card)

        # 4. Data & Backups
        data_card = self._create_card("Database & Backups", "Local SQLite database location and instant backup actions.")
        data_layout = QHBoxLayout(data_card)
        data_layout.setSpacing(12)

        backup_btn = QPushButton(" Create Backup Snapshot")
        backup_btn.setIcon(qta.icon("fa5s.database", color="#10B981"))
        backup_btn.setCursor(Qt.PointingHandCursor)
        backup_btn.clicked.connect(self.create_backup)
        data_layout.addWidget(backup_btn)

        restore_btn = QPushButton(" Restore From Backup")
        restore_btn.setIcon(qta.icon("fa5s.history", color="#F59E0B"))
        restore_btn.setCursor(Qt.PointingHandCursor)
        restore_btn.clicked.connect(self.restore_backup)
        data_layout.addWidget(restore_btn)
        data_layout.addStretch()

        layout.addWidget(data_card)

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _create_card(self, title: str, subtitle: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet("background: #181B22; border: 1px solid #282E3A; border-radius: 12px; padding: 18px;")
        return card

    def _on_theme_select(self, idx):
        theme_name = "dark" if idx == 0 else "light"
        self.theme_changed.emit(theme_name)

    def test_gemini(self):
        key = self.gemini_key.text().strip()
        ok, msg = GeminiService.test_connection(key)
        if ok:
            QMessageBox.information(self, "Gemini Connected", msg)
        else:
            QMessageBox.warning(self, "Gemini Test Result", msg)

    def test_groq(self):
        key = self.groq_key.text().strip()
        ok, msg = GroqService.test_connection(key)
        if ok:
            QMessageBox.information(self, "Groq Connected", msg)
        else:
            QMessageBox.warning(self, "Groq Test Result", msg)

    def test_ollama(self):
        url = self.ollama_url.text().strip()
        ok, msg, models = OllamaService.test_connection(url)
        if ok:
            models_str = "\n• " + "\n• ".join(models) if models else "\n(No models downloaded yet)"
            QMessageBox.information(self, "Ollama Connected", f"{msg}\nInstalled Models:{models_str}")
        else:
            QMessageBox.warning(self, "Ollama Test Result", msg)

    def create_backup(self):
        from services.backup_service import BackupService
        ok, msg = BackupService.create_backup("manual")
        if ok:
            QMessageBox.information(self, "Backup Complete", msg)
        else:
            QMessageBox.warning(self, "Backup Failed", msg)

    def restore_backup(self):
        from services.backup_service import BackupService
        from PySide6.QtWidgets import QFileDialog

        backups = BackupService.list_backups()
        if not backups:
            QMessageBox.information(self, "No Backups", "No database snapshots found yet. Click 'Create Backup Snapshot' first.")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Backup Database to Restore",
            str(BACKUP_DIR),
            "Database Files (*.db)"
        )
        if file_path:
            reply = QMessageBox.question(
                self,
                "Confirm Database Restore",
                f"Are you sure you want to restore from:\n{file_path}?\n\n"
                "A safety backup of your current database will be saved before restoring.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                ok, msg = BackupService.restore_backup(file_path)
                if ok:
                    QMessageBox.information(self, "Restore Succeeded", msg + "\nPlease restart FreelancePilot to reload data.")
                else:
                    QMessageBox.critical(self, "Restore Error", msg)

    def load_settings(self):
        db = SessionLocal()
        try:
            settings = {s.key: s.value for s in db.query(Setting).all()}
            if "business_name" in settings:
                self.biz_name.setText(settings["business_name"])
            if "business_email" in settings:
                self.biz_email.setText(settings["business_email"])
            if "business_phone" in settings:
                self.biz_phone.setText(settings["business_phone"])
            if "ollama_host" in settings:
                self.ollama_url.setText(settings["ollama_host"])

            # Load secure API keys from Keyring
            self.gemini_key.setText(AIProviderManager.get_api_key("gemini") or "")
            self.groq_key.setText(AIProviderManager.get_api_key("groq") or "")
        finally:
            db.close()

    def save_settings(self):
        db = SessionLocal()
        try:
            def _upsert(k, v):
                s = db.query(Setting).filter(Setting.key == k).first()
                if s:
                    s.value = v
                else:
                    db.add(Setting(key=k, value=v))

            _upsert("business_name", self.biz_name.text().strip())
            _upsert("business_email", self.biz_email.text().strip())
            _upsert("business_phone", self.biz_phone.text().strip())
            _upsert("ollama_host", self.ollama_url.text().strip())

            # Map provider combo
            p_map = {0: "gemini", 1: "groq", 2: "ollama"}
            _upsert("default_ai_provider", p_map.get(self.primary_ai_combo.currentIndex(), "gemini"))

            f_map = {0: "groq", 1: "gemini", 2: "ollama", 3: ""}
            _upsert("fallback_ai_provider", f_map.get(self.fallback_ai_combo.currentIndex(), "groq"))

            db.commit()

            # Save API keys securely to Keyring
            AIProviderManager.set_api_key("gemini", self.gemini_key.text().strip())
            AIProviderManager.set_api_key("groq", self.groq_key.text().strip())

            QMessageBox.information(self, "Saved", "All settings and API keys securely saved!")
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")
        finally:
            db.close()
