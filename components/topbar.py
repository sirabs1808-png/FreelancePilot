"""
Top navigation bar component for FreelancePilot.
Includes global search, quick action buttons, theme toggler, and notification bell.
"""

from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import qtawesome as qta


class Topbar(QFrame):
    """
    Application top bar for search, quick actions, theme toggle, and status.
    """
    search_triggered = Signal(str)
    new_invoice_clicked = Signal()
    new_project_clicked = Signal()
    ai_shortcut_clicked = Signal()
    theme_toggled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("topbarFrame")
        self.setFixedHeight(64)
        self.is_dark = True

        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 10, 24, 10)
        layout.setSpacing(14)

        # Global Search Bar
        self.search_container = QFrame()
        self.search_container.setStyleSheet("""
            QFrame {
                background-color: #181B22;
                border: 1px solid #282E3A;
                border-radius: 8px;
            }
            QFrame:focus-within {
                border: 1px solid #2563EB;
            }
        """)
        search_layout = QHBoxLayout(self.search_container)
        search_layout.setContentsMargins(10, 4, 10, 4)
        search_layout.setSpacing(8)

        search_icon = QLabel()
        search_icon.setPixmap(qta.icon("fa5s.search", color="#64748B").pixmap(14, 14))
        search_icon.setStyleSheet("border: none; background: transparent;")
        search_layout.addWidget(search_icon)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search clients, projects, invoices, or type Ctrl+K...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #F8FAFC;
                font-size: 13px;
                padding: 4px;
            }
        """)
        self.search_input.setFixedWidth(320)
        self.search_input.textChanged.connect(self.search_triggered.emit)
        search_layout.addWidget(self.search_input)

        # Shortcut hint
        hint = QLabel("Ctrl+K")
        hint.setStyleSheet("""
            color: #64748B;
            background: #1D2128;
            border: 1px solid #282E3A;
            border-radius: 4px;
            padding: 2px 6px;
            font-size: 10px;
            font-weight: bold;
        """)
        search_layout.addWidget(hint)

        layout.addWidget(self.search_container)

        # AI Status Pill
        self.ai_status_pill = QFrame()
        self.ai_status_pill.setStyleSheet("""
            QFrame {
                background: #10B98115;
                border: 1px solid #10B98133;
                border-radius: 14px;
                padding: 4px 10px;
            }
        """)
        ai_layout = QHBoxLayout(self.ai_status_pill)
        ai_layout.setContentsMargins(6, 2, 8, 2)
        ai_layout.setSpacing(6)

        dot = QLabel("●")
        dot.setStyleSheet("color: #10B981; font-size: 10px; border: none; background: transparent;")
        ai_layout.addWidget(dot)

        self.ai_status_lbl = QLabel("AI: Gemini Free")
        self.ai_status_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
        self.ai_status_lbl.setStyleSheet("color: #10B981; border: none; background: transparent;")
        ai_layout.addWidget(self.ai_status_lbl)

        layout.addWidget(self.ai_status_pill)

        layout.addStretch()

        # Theme Switcher Button
        self.theme_btn = QPushButton()
        self.theme_btn.setFixedSize(36, 36)
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.setToolTip("Toggle Dark / Light Theme")
        self.theme_btn.setIcon(qta.icon("fa5s.moon", color="#F8FAFC"))
        self.theme_btn.setStyleSheet("""
            QPushButton {
                background-color: #1D2128;
                border: 1px solid #282E3A;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #282E3A;
                border-color: #363E4E;
            }
        """)
        self.theme_btn.clicked.connect(self._toggle_theme)
        layout.addWidget(self.theme_btn)

        # Notification Bell
        self.notif_btn = QPushButton()
        self.notif_btn.setFixedSize(36, 36)
        self.notif_btn.setCursor(Qt.PointingHandCursor)
        self.notif_btn.setToolTip("Notifications (3 unread)")
        self.notif_btn.setIcon(qta.icon("fa5s.bell", color="#94A3B8"))
        self.notif_btn.setStyleSheet("""
            QPushButton {
                background-color: #1D2128;
                border: 1px solid #282E3A;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #282E3A;
                border-color: #363E4E;
            }
        """)
        layout.addWidget(self.notif_btn)

        # AI Assistant Shortcut Button
        ai_btn = QPushButton(" AI Assistant")
        ai_btn.setIcon(qta.icon("fa5s.magic", color="#FFFFFF"))
        ai_btn.setObjectName("primaryButton")
        ai_btn.setCursor(Qt.PointingHandCursor)
        ai_btn.clicked.connect(self.ai_shortcut_clicked.emit)
        layout.addWidget(ai_btn)

        # New Invoice Quick Action
        new_inv_btn = QPushButton(" + New Invoice")
        new_inv_btn.setCursor(Qt.PointingHandCursor)
        new_inv_btn.setStyleSheet("""
            QPushButton {
                background-color: #1D2128;
                color: #F8FAFC;
                border: 1px solid #282E3A;
                border-radius: 8px;
                padding: 8px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #282E3A;
                border-color: #363E4E;
            }
        """)
        new_inv_btn.clicked.connect(self.new_invoice_clicked.emit)
        layout.addWidget(new_inv_btn)

    def _toggle_theme(self):
        self.is_dark = not self.is_dark
        icon_name = "fa5s.moon" if self.is_dark else "fa5s.sun"
        icon_color = "#F8FAFC" if self.is_dark else "#F59E0B"
        self.theme_btn.setIcon(qta.icon(icon_name, color=icon_color))
        self.theme_toggled.emit()
