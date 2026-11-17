"""
Interactive and modern revenue chart component for FreelancePilot.
Built with clean QPainter vector graphics for high-DPI crispness and smooth gradients.
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QLinearGradient, QFont, QPainterPath
)


class RevenueChartWidget(QWidget):
    """
    Modern bar & area chart visualizing monthly revenue and expenses.
    Renders with rounded bars, smooth linear gradients, and subtle grid lines.
    """
    def __init__(self, data: list = None, parent: QWidget = None):
        super().__init__(parent)
        self.setMinimumHeight(240)
        self.hover_index = -1

        # Default sample 6-month financial data (month, income, expense)
        self.data = data or [
            {"month": "Jun", "income": 4200, "expense": 1100},
            {"month": "Jul", "income": 5800, "expense": 1400},
            {"month": "Aug", "income": 7100, "expense": 1650},
            {"month": "Sep", "income": 6400, "expense": 1200},
            {"month": "Oct", "income": 8900, "expense": 1950},
            {"month": "Nov", "income": 10450, "expense": 2100},
        ]

    def set_data(self, data: list):
        self.data = data
        self.update()

    def paintEvent(self, event):
        if not self.data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        padding_left = 60
        padding_right = 30
        padding_top = 35
        padding_bottom = 40

        chart_w = w - padding_left - padding_right
        chart_h = h - padding_top - padding_bottom

        # Find maximum value for scaling
        max_val = max(max(d["income"] for d in self.data), 1000)
        max_val = int(max_val * 1.2)  # 20% headroom

        # Draw grid lines & Y-axis labels
        grid_steps = 4
        painter.setFont(QFont("Segoe UI", 9))
        grid_pen = QPen(QColor("#282E3A"), 1, Qt.DashLine)
        text_pen = QPen(QColor("#64748B"))

        for i in range(grid_steps + 1):
            y_val = int(max_val * (i / grid_steps))
            y_pos = padding_top + chart_h - (chart_h * (i / grid_steps))

            # Grid line
            painter.setPen(grid_pen)
            painter.drawLine(padding_left, int(y_pos), int(w - padding_right), int(y_pos))

            # Y-axis text
            painter.setPen(text_pen)
            painter.drawText(
                QRectF(0, y_pos - 8, padding_left - 12, 16),
                Qt.AlignRight | Qt.AlignVCenter,
                f"${y_val:,.0f}"
            )

        # Draw Bars for each month
        n = len(self.data)
        bar_group_w = chart_w / n
        bar_w = min(22.0, bar_group_w * 0.28)
        spacing = 6.0

        for idx, item in enumerate(self.data):
            group_center = padding_left + (idx + 0.5) * bar_group_w

            # Income Bar (Electric Blue Gradient)
            income_h = (item["income"] / max_val) * chart_h
            income_x = group_center - bar_w - (spacing / 2)
            income_y = padding_top + chart_h - income_h

            income_rect = QRectF(income_x, income_y, bar_w, income_h)
            grad_inc = QLinearGradient(income_x, income_y, income_x, income_y + income_h)
            grad_inc.setColorAt(0, QColor("#3B82F6"))
            grad_inc.setColorAt(1, QColor("#1D4ED8"))

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(grad_inc))
            path_inc = QPainterPath()
            path_inc.addRoundedRect(income_rect, 5, 5)
            painter.drawPath(path_inc)

            # Expense Bar (Violet Gradient)
            expense_h = (item["expense"] / max_val) * chart_h
            expense_x = group_center + (spacing / 2)
            expense_y = padding_top + chart_h - expense_h

            expense_rect = QRectF(expense_x, expense_y, bar_w, expense_h)
            grad_exp = QLinearGradient(expense_x, expense_y, expense_x, expense_y + expense_h)
            grad_exp.setColorAt(0, QColor("#A855F7"))
            grad_exp.setColorAt(1, QColor("#6B21A8"))

            painter.setBrush(QBrush(grad_exp))
            path_exp = QPainterPath()
            path_exp.addRoundedRect(expense_rect, 5, 5)
            painter.drawPath(path_exp)

            # X-axis Month Label
            painter.setPen(text_pen)
            painter.drawText(
                QRectF(group_center - (bar_group_w / 2), h - padding_bottom + 10, bar_group_w, 20),
                Qt.AlignCenter,
                item["month"]
            )

        # Legend in top right
        legend_x = w - padding_right - 180
        legend_y = 12

        # Income legend
        painter.setBrush(QColor("#3B82F6"))
        painter.drawRoundedRect(QRectF(legend_x, legend_y + 3, 10, 10), 2, 2)
        painter.setPen(QColor("#94A3B8"))
        painter.drawText(QRectF(legend_x + 16, legend_y, 65, 16), Qt.AlignLeft | Qt.AlignVCenter, "Income")

        # Expense legend
        painter.setBrush(QColor("#A855F7"))
        painter.drawRoundedRect(QRectF(legend_x + 85, legend_y + 3, 10, 10), 2, 2)
        painter.drawText(QRectF(legend_x + 101, legend_y, 75, 16), Qt.AlignLeft | Qt.AlignVCenter, "Expenses")
