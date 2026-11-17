"""
Reusable UI Card Components for FreelancePilot.
Designed with modern aesthetics: rounded corners, crisp borders, subtle hover effects.
"""

from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
import qtawesome as qta
from utils.config import DARK_THEME


class StatCard(QFrame):
    """
    Modern statistic card showing metric, value, trend badge, and icon.
    Inspired by Linear and Stripe analytics cards.
    """
    def __init__(
        self,
        title: str,
        value: str,
        icon_name: str,
        trend: str = "",
        trend_positive: bool = True,
        accent_color: str = "#2563EB",
        parent: QWidget = None
    ):
        super().__init__(parent)
        self.setObjectName("cardFrame")
        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedHeight(125)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)

        # Top Row: Title + Icon Badge
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        title_label.setStyleSheet("color: #94A3B8; background: transparent; border: none;")
        top_row.addWidget(title_label)
        top_row.addStretch()

        # Icon with rounded badge background
        icon_badge = QLabel()
        icon_badge.setFixedSize(36, 36)
        icon_badge.setAlignment(Qt.AlignCenter)
        icon_badge.setStyleSheet(f"""
            background-color: {accent_color}22;
            border: 1px solid {accent_color}44;
            border-radius: 8px;
        """)
        pixmap = qta.icon(icon_name, color=accent_color).pixmap(18, 18)
        icon_badge.setPixmap(pixmap)
        top_row.addWidget(icon_badge)

        layout.addLayout(top_row)

        # Value Row
        self.value_label = QLabel(value)
        self.value_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.value_label.setStyleSheet("color: #F8FAFC; background: transparent; border: none;")
        layout.addWidget(self.value_label)

        # Bottom Row: Trend / Subtitle
        if trend:
            bottom_row = QHBoxLayout()
            trend_color = "#10B981" if trend_positive else "#EF4444"
            trend_icon = "fa5s.arrow-up" if trend_positive else "fa5s.arrow-down"

            trend_badge = QLabel()
            trend_badge.setStyleSheet(f"""
                color: {trend_color};
                background: {trend_color}18;
                border-radius: 4px;
                padding: 2px 6px;
                font-size: 11px;
                font-weight: 600;
            """)
            trend_badge.setText(f"{trend}")
            bottom_row.addWidget(trend_badge)
            bottom_row.addStretch()
            layout.addLayout(bottom_row)
        else:
            layout.addStretch()

    def update_value(self, new_value: str):
        self.value_label.setText(new_value)


class ModernCard(QFrame):
    """
    General container card with header, subtitle, and body.
    """
    def __init__(self, title: str = "", subtitle: str = "", parent: QWidget = None):
        super().__init__(parent)
        self.setObjectName("cardFrame")
        self.setFrameShape(QFrame.StyledPanel)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 18, 20, 18)
        self.main_layout.setSpacing(14)

        if title:
            header_layout = QHBoxLayout()
            header_layout.setSpacing(8)

            title_col = QVBoxLayout()
            title_col.setSpacing(2)

            title_lbl = QLabel(title)
            title_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            title_lbl.setStyleSheet("color: #F8FAFC; background: transparent; border: none;")
            title_col.addWidget(title_lbl)

            if subtitle:
                sub_lbl = QLabel(subtitle)
                sub_lbl.setFont(QFont("Segoe UI", 9))
                sub_lbl.setStyleSheet("color: #64748B; background: transparent; border: none;")
                title_col.addWidget(sub_lbl)

            header_layout.addLayout(title_col)
            header_layout.addStretch()

            self.header_action_layout = QHBoxLayout()
            header_layout.addLayout(self.header_action_layout)

            self.main_layout.addLayout(header_layout)

        # Body container
        self.body_layout = QVBoxLayout()
        self.body_layout.setSpacing(10)
        self.main_layout.addLayout(self.body_layout)

    def add_header_action(self, widget: QWidget):
        self.header_action_layout.addWidget(widget)

    def add_widget(self, widget: QWidget):
        self.body_layout.addWidget(widget)

    def add_layout(self, layout):
        self.body_layout.addLayout(layout)


class StatusBadge(QLabel):
    """
    Status badge for project, task, and invoice statuses.
    """
    COLORS = {
        "Paid": ("#10B981", "#10B98122"),
        "Completed": ("#10B981", "#10B98122"),
        "In Progress": ("#3B82F6", "#3B82F622"),
        "Sent": ("#06B6D4", "#06B6D422"),
        "Draft": ("#94A3B8", "#94A3B822"),
        "On Hold": ("#F59E0B", "#F59E0B22"),
        "Urgent": ("#EF4444", "#EF444422"),
        "High": ("#F97316", "#F9731622"),
        "Medium": ("#FBBF24", "#FBBF2422"),
        "Low": ("#64748B", "#64748B22"),
        "Overdue": ("#EF4444", "#EF444422"),
        "Cancelled": ("#6B7280", "#6B728022"),
    }

    def __init__(self, text: str, parent: QWidget = None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))

        fg, bg = self.COLORS.get(text, ("#94A3B8", "#94A3B822"))
        self.setStyleSheet(f"""
            color: {fg};
            background-color: {bg};
            border: 1px solid {fg}44;
            border-radius: 6px;
            padding: 3px 8px;
        """)
