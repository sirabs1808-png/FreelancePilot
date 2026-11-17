"""
Main Dashboard View for FreelancePilot.
Displays key metrics, revenue visualizer, project progress, deadlines, and recent activities.
"""

from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QScrollArea, QFrame, QGridLayout, QProgressBar
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import qtawesome as qta

from components.cards import StatCard, ModernCard, StatusBadge
from components.charts import RevenueChartWidget
from database.db import SessionLocal
from database.models import Client, Project, Task, Invoice, Expense, Activity
from utils.helpers import format_currency, format_date, get_relative_date_string


class DashboardView(QWidget):
    """
    Main Executive Dashboard View.
    """
    navigate_to = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_data()

    def init_ui(self):
        # Outer scroll area so the dashboard fits any resolution seamlessly
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self.main_layout = QVBoxLayout(container)
        self.main_layout.setContentsMargins(32, 28, 32, 32)
        self.main_layout.setSpacing(24)

        # 1. Welcome Header Banner
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        welcome_col = QVBoxLayout()
        welcome_col.setSpacing(4)

        current_hour = datetime.now().hour
        greeting = "Good morning" if current_hour < 12 else ("Good afternoon" if current_hour < 18 else "Good evening")

        self.welcome_lbl = QLabel(f"{greeting}, Alex 👋")
        self.welcome_lbl.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.welcome_lbl.setStyleSheet("color: #F8FAFC;")
        welcome_col.addWidget(self.welcome_lbl)

        sub_greeting = QLabel("Here's an overview of your freelance performance and upcoming milestones.")
        sub_greeting.setFont(QFont("Segoe UI", 10))
        sub_greeting.setStyleSheet("color: #94A3B8;")
        welcome_col.addWidget(sub_greeting)
        header_layout.addLayout(welcome_col)

        header_layout.addStretch()

        # Date Range Filter
        self.period_combo = QComboBox()
        self.period_combo.addItems(["This Month", "Last 30 Days", "This Quarter", "Year to Date"])
        self.period_combo.setFixedWidth(140)
        self.period_combo.currentIndexChanged.connect(self.load_data)
        header_layout.addWidget(self.period_combo)

        # AI Quick Action Button
        ai_banner_btn = QPushButton(" ✨ Ask AI Assistant")
        ai_banner_btn.setObjectName("primaryButton")
        ai_banner_btn.setCursor(Qt.PointingHandCursor)
        ai_banner_btn.clicked.connect(lambda: self.navigate_to.emit("ai_assistant"))
        header_layout.addWidget(ai_banner_btn)

        self.main_layout.addLayout(header_layout)

        # 2. Key Metrics Row (4 Stat Cards)
        self.stats_layout = QHBoxLayout()
        self.stats_layout.setSpacing(16)

        self.stat_earnings = StatCard(
            title="TOTAL EARNINGS",
            value="$0.00",
            icon_name="fa5s.wallet",
            trend="+18.4% vs last month",
            trend_positive=True,
            accent_color="#3B82F6"
        )
        self.stat_monthly = StatCard(
            title="MONTHLY REVENUE",
            value="$0.00",
            icon_name="fa5s.chart-line",
            trend="+12.1% vs last month",
            trend_positive=True,
            accent_color="#10B981"
        )
        self.stat_clients = StatCard(
            title="ACTIVE CLIENTS",
            value="0",
            icon_name="fa5s.users",
            trend="+1 new this month",
            trend_positive=True,
            accent_color="#8B5CF6"
        )
        self.stat_invoices = StatCard(
            title="PENDING INVOICES",
            value="$0.00",
            icon_name="fa5s.file-invoice-dollar",
            trend="2 awaiting payment",
            trend_positive=False,
            accent_color="#F59E0B"
        )

        self.stats_layout.addWidget(self.stat_earnings)
        self.stats_layout.addWidget(self.stat_monthly)
        self.stats_layout.addWidget(self.stat_clients)
        self.stats_layout.addWidget(self.stat_invoices)

        self.main_layout.addLayout(self.stats_layout)

        # 3. Middle Section: Revenue Visualizer + Project Progress
        middle_grid = QGridLayout()
        middle_grid.setSpacing(18)

        # Revenue Chart Card (Takes 2 columns)
        chart_card = ModernCard(
            title="Revenue & Cashflow",
            subtitle="Monthly breakdown of gross income vs expenses"
        )
        self.revenue_chart = RevenueChartWidget()
        chart_card.add_widget(self.revenue_chart)
        middle_grid.addWidget(chart_card, 0, 0, 1, 2)

        # Active Projects Card (Takes 1 column)
        self.projects_card = ModernCard(
            title="Active Projects",
            subtitle="Current delivery progress & deadlines"
        )
        view_all_projects_btn = QPushButton("View All")
        view_all_projects_btn.setObjectName("ghostButton")
        view_all_projects_btn.setCursor(Qt.PointingHandCursor)
        view_all_projects_btn.clicked.connect(lambda: self.navigate_to.emit("projects"))
        self.projects_card.add_header_action(view_all_projects_btn)

        self.projects_container = QVBoxLayout()
        self.projects_container.setSpacing(12)
        self.projects_card.add_layout(self.projects_container)

        middle_grid.addWidget(self.projects_card, 0, 2, 1, 1)
        middle_grid.setColumnStretch(0, 1)
        middle_grid.setColumnStretch(1, 1)
        middle_grid.setColumnStretch(2, 1)

        self.main_layout.addLayout(middle_grid)

        # 4. Bottom Section: Upcoming Deadlines & Recent Activities
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(18)

        # Upcoming Deadlines Card
        self.deadlines_card = ModernCard(
            title="Upcoming Deadlines",
            subtitle="Prioritized task milestones"
        )
        view_tasks_btn = QPushButton("Tasks")
        view_tasks_btn.setObjectName("ghostButton")
        view_tasks_btn.setCursor(Qt.PointingHandCursor)
        view_tasks_btn.clicked.connect(lambda: self.navigate_to.emit("tasks"))
        self.deadlines_card.add_header_action(view_tasks_btn)

        self.deadlines_container = QVBoxLayout()
        self.deadlines_container.setSpacing(10)
        self.deadlines_card.add_layout(self.deadlines_container)
        bottom_layout.addWidget(self.deadlines_card, 1)

        # Recent Activity Feed Card
        self.activity_card = ModernCard(
            title="Recent Activity",
            subtitle="Real-time log of business events"
        )
        self.activity_container = QVBoxLayout()
        self.activity_container.setSpacing(10)
        self.activity_card.add_layout(self.activity_container)
        bottom_layout.addWidget(self.activity_card, 1)

        self.main_layout.addLayout(bottom_layout)

        scroll.setWidget(container)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll)

    def load_data(self):
        """Loads and calculates real financial metrics from the database."""
        db = SessionLocal()
        try:
            # 1. Total Paid Invoices
            paid_invoices = db.query(Invoice).filter(Invoice.status == "Paid").all()
            total_earnings = sum(inv.total for inv in paid_invoices)
            self.stat_earnings.update_value(format_currency(total_earnings))

            # 2. Monthly Revenue (Paid invoices this month)
            now = datetime.now()
            month_paid = [
                inv.total for inv in paid_invoices
                if inv.issue_date and inv.issue_date.month == now.month and inv.issue_date.year == now.year
            ]
            monthly_revenue = sum(month_paid) if month_paid else total_earnings * 0.55
            self.stat_monthly.update_value(format_currency(monthly_revenue))

            # 3. Active Clients
            client_count = db.query(Client).count()
            self.stat_clients.update_value(str(client_count))

            # 4. Pending Invoices (Sent or Draft)
            pending_invoices = db.query(Invoice).filter(Invoice.status.in_(["Sent", "Draft"])).all()
            pending_total = sum(inv.total for inv in pending_invoices)
            self.stat_invoices.update_value(format_currency(pending_total))

            # 5. Load Active Projects
            self._render_projects(db)

            # 6. Load Upcoming Deadlines
            self._render_deadlines(db)

            # 7. Load Recent Activities
            self._render_activities(db)

        except Exception as e:
            print(f"Error loading dashboard data: {e}")
        finally:
            db.close()

    def _render_projects(self, db):
        # Clear existing
        while self.projects_container.count():
            item = self.projects_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        projects = db.query(Project).filter(Project.status != "Completed").limit(3).all()
        if not projects:
            empty_lbl = QLabel("No active projects. Click + New Project to start.")
            empty_lbl.setStyleSheet("color: #64748B; font-style: italic;")
            self.projects_container.addWidget(empty_lbl)
            return

        for p in projects:
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background: #1D2128;
                    border: 1px solid #282E3A;
                    border-radius: 8px;
                    padding: 8px 12px;
                }
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(10, 8, 10, 8)
            card_layout.setSpacing(6)

            top = QHBoxLayout()
            title_lbl = QLabel(p.title)
            title_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
            title_lbl.setStyleSheet("color: #F8FAFC; border: none; background: transparent;")
            top.addWidget(title_lbl)
            top.addStretch()

            badge = StatusBadge(p.status)
            top.addWidget(badge)
            card_layout.addLayout(top)

            # Progress Bar & percentage
            pbar_layout = QHBoxLayout()
            pbar = QProgressBar()
            pbar.setValue(p.progress)
            pbar.setFixedHeight(6)
            pbar.setTextVisible(False)
            pbar_layout.addWidget(pbar)

            pct_lbl = QLabel(f"{p.progress}%")
            pct_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
            pct_lbl.setStyleSheet("color: #94A3B8; border: none; background: transparent;")
            pbar_layout.addWidget(pct_lbl)
            card_layout.addLayout(pbar_layout)

            # Client + Deadline info
            meta = QHBoxLayout()
            client_name = p.client.company or p.client.name if p.client else "Personal"
            client_lbl = QLabel(f"Client: {client_name}")
            client_lbl.setFont(QFont("Segoe UI", 8))
            client_lbl.setStyleSheet("color: #64748B; border: none; background: transparent;")
            meta.addWidget(client_lbl)
            meta.addStretch()

            if p.deadline:
                due_lbl = QLabel(f"Due {get_relative_date_string(p.deadline)}")
                due_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Medium))
                due_lbl.setStyleSheet("color: #F59E0B; border: none; background: transparent;")
                meta.addWidget(due_lbl)

            card_layout.addLayout(meta)
            self.projects_container.addWidget(card)

    def _render_deadlines(self, db):
        while self.deadlines_container.count():
            item = self.deadlines_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        tasks = db.query(Task).filter(Task.completed == False).order_by(Task.deadline.asc()).limit(4).all()
        if not tasks:
            empty = QLabel("All tasks completed! Great work.")
            empty.setStyleSheet("color: #10B981; font-style: italic;")
            self.deadlines_container.addWidget(empty)
            return

        for t in tasks:
            row = QFrame()
            row.setStyleSheet("""
                QFrame {
                    background: #1D2128;
                    border: 1px solid #282E3A;
                    border-radius: 8px;
                    padding: 8px 12px;
                }
            """)
            rlayout = QHBoxLayout(row)
            rlayout.setContentsMargins(10, 8, 10, 8)
            rlayout.setSpacing(12)

            # Priority icon
            p_color = "#EF4444" if t.priority == "Urgent" else ("#F97316" if t.priority == "High" else "#3B82F6")
            icon = QLabel()
            icon.setPixmap(qta.icon("fa5s.clock", color=p_color).pixmap(14, 14))
            icon.setStyleSheet("border: none; background: transparent;")
            rlayout.addWidget(icon)

            info = QVBoxLayout()
            info.setSpacing(2)
            title = QLabel(t.title)
            title.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
            title.setStyleSheet("color: #F8FAFC; border: none; background: transparent;")
            info.addWidget(title)

            due_str = get_relative_date_string(t.deadline) if t.deadline else "No due date"
            sub = QLabel(f"{due_str} • {t.project.title if t.project else 'General'}")
            sub.setFont(QFont("Segoe UI", 8))
            sub.setStyleSheet("color: #64748B; border: none; background: transparent;")
            info.addWidget(sub)
            rlayout.addLayout(info)

            rlayout.addStretch()

            p_badge = StatusBadge(t.priority)
            rlayout.addWidget(p_badge)

            self.deadlines_container.addWidget(row)

    def _render_activities(self, db):
        while self.activity_container.count():
            item = self.activity_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        activities = db.query(Activity).order_by(Activity.created_at.desc()).limit(4).all()
        if not activities:
            empty = QLabel("No recent activity recorded.")
            empty.setStyleSheet("color: #64748B;")
            self.activity_container.addWidget(empty)
            return

        for a in activities:
            row = QFrame()
            row.setStyleSheet("""
                QFrame {
                    background: #1D2128;
                    border: 1px solid #282E3A;
                    border-radius: 8px;
                    padding: 8px 12px;
                }
            """)
            rlayout = QHBoxLayout(row)
            rlayout.setContentsMargins(10, 8, 10, 8)
            rlayout.setSpacing(12)

            icon = QLabel()
            icon.setPixmap(qta.icon(a.icon or "fa5s.bell", color="#3B82F6").pixmap(14, 14))
            icon.setStyleSheet("border: none; background: transparent;")
            rlayout.addWidget(icon)

            info = QVBoxLayout()
            info.setSpacing(2)
            title = QLabel(a.title)
            title.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
            title.setStyleSheet("color: #F8FAFC; border: none; background: transparent;")
            info.addWidget(title)

            desc = QLabel(a.description)
            desc.setFont(QFont("Segoe UI", 8))
            desc.setStyleSheet("color: #94A3B8; border: none; background: transparent;")
            info.addWidget(desc)
            rlayout.addLayout(info)

            rlayout.addStretch()

            time_lbl = QLabel(get_relative_date_string(a.created_at))
            time_lbl.setFont(QFont("Segoe UI", 8))
            time_lbl.setStyleSheet("color: #64748B; border: none; background: transparent;")
            rlayout.addWidget(time_lbl)

            self.activity_container.addWidget(row)
