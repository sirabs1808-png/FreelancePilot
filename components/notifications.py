"""
Toast Notification Component for FreelancePilot.
Displays modern, animated, auto-dismissing toast notifications.
"""

from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout, QPushButton, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QFont
import qtawesome as qta


class ToastNotification(QFrame):
    """
    Floating, self-dismissing toast notification alert.
    """
    ICONS = {
        "success": ("fa5s.check-circle", "#10B981", "#10B9811A", "#10B9814D"),
        "error": ("fa5s.exclamation-circle", "#EF4444", "#EF44441A", "#EF44444D"),
        "warning": ("fa5s.exclamation-triangle", "#F59E0B", "#F59E0B1A", "#F59E0B4D"),
        "info": ("fa5s.info-circle", "#3B82F6", "#3B82F61A", "#3B82F64D"),
    }

    def __init__(self, message: str, toast_type: str = "success", duration_ms: int = 3500, parent=None):
        super().__init__(parent)
        self.duration_ms = duration_ms

        icon_name, fg_color, bg_color, border_color = self.ICONS.get(
            toast_type.lower(), self.ICONS["info"]
        )

        self.setStyleSheet(f"""
            QFrame {{
                background-color: #1A1D24;
                border: 1px solid {border_color};
                border-left: 4px solid {fg_color};
                border-radius: 8px;
            }}
        """)
        self.setFixedHeight(50)
        self.setMinimumWidth(280)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 12, 8)
        layout.setSpacing(10)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon(icon_name, color=fg_color).pixmap(18, 18))
        icon_lbl.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(icon_lbl)

        msg_lbl = QLabel(message)
        msg_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        msg_lbl.setStyleSheet("color: #F8FAFC; border: none; background: transparent;")
        layout.addWidget(msg_lbl)

        layout.addStretch()

        close_btn = QPushButton()
        close_btn.setFixedSize(20, 20)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setIcon(qta.icon("fa5s.times", color="#94A3B8"))
        close_btn.setStyleSheet("background: transparent; border: none;")
        close_btn.clicked.connect(self.dismiss)
        layout.addWidget(close_btn)

        # Opacity effect for fade out
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)

        # Auto-dismiss timer
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.fade_out)
        self.timer.start(self.duration_ms)

    def fade_out(self):
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(300)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.finished.connect(self.dismiss)
        self.anim.start()

    def dismiss(self):
        self.timer.stop()
        self.deleteLater()
