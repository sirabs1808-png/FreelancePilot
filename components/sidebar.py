"""
Collapsible left sidebar navigation component for FreelancePilot.
Supports smooth collapsing, active state highlighting, tooltips, and badges.
"""

from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon
import qtawesome as qta


class NavItemButton(QPushButton):
    """
    Individual navigation item button in the sidebar.
    """
    def __init__(self, key: str, label: str, icon_name: str, parent=None):
        super().__init__(parent)
        self.key = key
        self.label_text = label
        self.icon_name = icon_name
        self.is_active = False
        self.is_collapsed = False

        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(44)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.normal_icon = qta.icon(self.icon_name, color="#94A3B8")
        self.active_icon = qta.icon(self.icon_name, color="#3B82F6")

        self.setIcon(self.normal_icon)
        self.setIconSize(self.iconSize())
        self.setText(f"   {self.label_text}")
        self.setToolTip(self.label_text)

        self.update_style()

    def set_collapsed(self, collapsed: bool):
        self.is_collapsed = collapsed
        if collapsed:
            self.setText("")
        else:
            self.setText(f"   {self.label_text}")

    def set_active(self, active: bool):
        self.is_active = active
        self.setChecked(active)
        self.setIcon(self.active_icon if active else self.normal_icon)
        self.update_style()

    def update_style(self):
        if self.is_active:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #2563EB20;
                    color: #38BDF8;
                    border: 1px solid #2563EB40;
                    border-left: 3px solid #3B82F6;
                    border-radius: 8px;
                    text-align: left;
                    padding-left: 14px;
                    font-size: 13px;
                    font-weight: 600;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #94A3B8;
                    border: 1px solid transparent;
                    border-radius: 8px;
                    text-align: left;
                    padding-left: 14px;
                    font-size: 13px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #1D2128;
                    color: #F8FAFC;
                    border: 1px solid #282E3A;
                }
            """)


class Sidebar(QFrame):
    """
    Main Sidebar navigation container.
    """
    nav_changed = Signal(str)  # Emits page key (e.g., 'dashboard', 'clients')

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebarFrame")
        self.is_collapsed = False
        self.buttons = {}

        self.setFixedWidth(240)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(6)

        # Header / Brand Logo
        self.header_layout = QHBoxLayout()
        self.header_layout.setContentsMargins(4, 0, 4, 12)
        self.header_layout.setSpacing(10)

        # Brand Icon Badge
        self.logo_icon = QLabel()
        self.logo_icon.setFixedSize(36, 36)
        self.logo_icon.setAlignment(Qt.AlignCenter)
        self.logo_icon.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2563EB, stop:1 #7C3AED);
            border-radius: 9px;
        """)
        self.logo_icon.setPixmap(qta.icon("fa5s.paper-plane", color="#FFFFFF").pixmap(18, 18))
        self.header_layout.addWidget(self.logo_icon)

        # Brand Title & Version
        self.brand_info = QVBoxLayout()
        self.brand_info.setSpacing(1)
        self.brand_title = QLabel("FreelancePilot")
        self.brand_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.brand_title.setStyleSheet("color: #F8FAFC; border: none; background: transparent;")
        self.brand_sub = QLabel("AI Studio v1.0")
        self.brand_sub.setFont(QFont("Segoe UI", 9))
        self.brand_sub.setStyleSheet("color: #64748B; border: none; background: transparent;")
        self.brand_info.addWidget(self.brand_title)
        self.brand_info.addWidget(self.brand_sub)
        self.header_layout.addLayout(self.brand_info)

        self.header_layout.addStretch()

        # Collapse Button
        self.collapse_btn = QPushButton()
        self.collapse_btn.setFixedSize(28, 28)
        self.collapse_btn.setCursor(Qt.PointingHandCursor)
        self.collapse_btn.setIcon(qta.icon("fa5s.chevron-left", color="#94A3B8"))
        self.collapse_btn.setToolTip("Toggle Sidebar (Ctrl+B)")
        self.collapse_btn.setStyleSheet("""
            QPushButton {
                background: #1D2128;
                border: 1px solid #282E3A;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #2563EB;
                border-color: #3B82F6;
            }
        """)
        self.collapse_btn.clicked.connect(self.toggle_collapse)
        self.header_layout.addWidget(self.collapse_btn)

        layout.addLayout(self.header_layout)

        # Navigation Items List
        nav_definitions = [
            ("dashboard", "Dashboard", "fa5s.tachometer-alt"),
            ("ai_assistant", "AI Assistant", "fa5s.magic"),
            ("clients", "Clients", "fa5s.users"),
            ("projects", "Projects", "fa5s.layer-group"),
            ("tasks", "Tasks", "fa5s.tasks"),
            ("invoices", "Invoices", "fa5s.file-invoice-dollar"),
            ("expenses", "Expenses", "fa5s.receipt"),
            ("proposal_gen", "AI Proposals", "fa5s.file-contract"),
            ("seo_studio", "SEO Studio", "fa5s.search"),
            ("templates", "Templates", "fa5s.folder-open"),
            ("reports", "Reports", "fa5s.chart-bar"),
            ("settings", "Settings", "fa5s.cog"),
        ]

        # Scrollable container for navigation items
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        nav_container = QWidget()
        nav_container.setStyleSheet("background: transparent;")
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(4)

        for key, label, icon in nav_definitions:
            btn = NavItemButton(key, label, icon, self)
            btn.clicked.connect(lambda checked, k=key: self.on_item_clicked(k))
            self.buttons[key] = btn
            nav_layout.addWidget(btn)

        nav_layout.addStretch()
        scroll.setWidget(nav_container)
        layout.addWidget(scroll)

        # Bottom Profile Footer
        self.footer = QFrame()
        self.footer.setStyleSheet("""
            QFrame {
                background-color: #1D2128;
                border: 1px solid #282E3A;
                border-radius: 10px;
                padding: 4px;
            }
        """)
        footer_layout = QHBoxLayout(self.footer)
        footer_layout.setContentsMargins(8, 6, 8, 6)
        footer_layout.setSpacing(10)

        # Avatar
        self.avatar = QLabel()
        self.avatar.setFixedSize(30, 30)
        self.avatar.setStyleSheet("""
            background: #2563EB;
            color: #FFFFFF;
            font-weight: bold;
            border-radius: 15px;
        """)
        self.avatar.setAlignment(Qt.AlignCenter)
        self.avatar.setText("AR")
        footer_layout.addWidget(self.avatar)

        # User Info
        self.user_info = QVBoxLayout()
        self.user_info.setSpacing(1)
        self.user_name = QLabel("Alex Rivers")
        self.user_name.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.user_name.setStyleSheet("color: #F8FAFC; border: none; background: transparent;")
        self.user_badge = QLabel("PRO ACCOUNT")
        self.user_badge.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        self.user_badge.setStyleSheet("color: #10B981; border: none; background: transparent;")
        self.user_info.addWidget(self.user_name)
        self.user_info.addWidget(self.user_badge)
        footer_layout.addLayout(self.user_info)

        footer_layout.addStretch()
        layout.addWidget(self.footer)

        # Set default active
        self.set_active("dashboard")

    def toggle_collapse(self):
        self.is_collapsed = not self.is_collapsed
        if self.is_collapsed:
            self.setFixedWidth(72)
            self.brand_title.hide()
            self.brand_sub.hide()
            self.user_name.hide()
            self.user_badge.hide()
            self.collapse_btn.setIcon(qta.icon("fa5s.chevron-right", color="#94A3B8"))
            for btn in self.buttons.values():
                btn.set_collapsed(True)
        else:
            self.setFixedWidth(240)
            self.brand_title.show()
            self.brand_sub.show()
            self.user_name.show()
            self.user_badge.show()
            self.collapse_btn.setIcon(qta.icon("fa5s.chevron-left", color="#94A3B8"))
            for btn in self.buttons.values():
                btn.set_collapsed(False)

    def on_item_clicked(self, key: str):
        self.set_active(key)
        self.nav_changed.emit(key)

    def set_active(self, key: str):
        for k, btn in self.buttons.items():
            btn.set_active(k == key)
