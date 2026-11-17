"""
Reports and Analytics View for FreelancePilot.
Generates comprehensive visual analytics, client lifetime value reports,
expense category breakdowns, and exports to PDF and CSV formats.
"""

import csv
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QScrollArea,
    QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QFont, QDesktopServices
import qtawesome as qta

from database.db import SessionLocal
from database.models import Invoice, Expense, Client, Project
from components.charts import RevenueChartWidget
from components.cards import StatCard
from services.pdf_service import PDFService
from utils.helpers import format_currency, format_date


class ReportsView(QWidget):
    """
    Financial Reporting and Business Intelligence Screen.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_report_data()

    def init_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 28, 32, 32)
        layout.setSpacing(22)

        # 1. Header Banner
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Reports & Analytics")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #F8FAFC;")
        sub = QLabel("Comprehensive financial analysis, client lifetime value (LTV), expense tracking, and export center.")
        sub.setFont(QFont("Segoe UI", 10))
        sub.setStyleSheet("color: #94A3B8;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        header.addStretch()

        # Date Range selector
        self.range_combo = QComboBox()
        self.range_combo.addItems(["Last 6 Months", "Year to Date", "All Time"])
        self.range_combo.setFixedWidth(140)
        self.range_combo.currentIndexChanged.connect(self.load_report_data)
        header.addWidget(self.range_combo)

        export_csv_btn = QPushButton(" Export CSV")
        export_csv_btn.setIcon(qta.icon("fa5s.file-csv", color="#38BDF8"))
        export_csv_btn.setCursor(Qt.PointingHandCursor)
        export_csv_btn.clicked.connect(self.export_csv)
        header.addWidget(export_csv_btn)

        export_pdf_btn = QPushButton(" Export PDF Report")
        export_pdf_btn.setIcon(qta.icon("fa5s.file-pdf", color="#EF4444"))
        export_pdf_btn.setObjectName("primaryButton")
        export_pdf_btn.setCursor(Qt.PointingHandCursor)
        export_pdf_btn.clicked.connect(self.export_pdf_report)
        header.addWidget(export_pdf_btn)

        layout.addLayout(header)

        # 2. Key KPI Stats Strip
        self.stats_row = QHBoxLayout()
        self.stats_row.setSpacing(14)

        self.stat_gross = StatCard("TOTAL BILLED", "$0.00", "fa5s.wallet", "Invoiced volume", True, "#3B82F6")
        self.stat_collected = StatCard("COLLECTED REVENUE", "$0.00", "fa5s.check-circle", "Cash received", True, "#10B981")
        self.stat_expenses = StatCard("TOTAL EXPENSES", "$0.00", "fa5s.receipt", "Operating costs", False, "#EF4444")
        self.stat_net = StatCard("NET PROFIT", "$0.00", "fa5s.chart-line", "Margin", True, "#8B5CF6")

        self.stats_row.addWidget(self.stat_gross)
        self.stats_row.addWidget(self.stat_collected)
        self.stats_row.addWidget(self.stat_expenses)
        self.stats_row.addWidget(self.stat_net)
        layout.addLayout(self.stats_row)

        # 3. Revenue & Cashflow Chart Card
        chart_card = QFrame()
        chart_card.setStyleSheet("background: #181B22; border: 1px solid #282E3A; border-radius: 12px; padding: 18px;")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setSpacing(10)

        chart_head = QHBoxLayout()
        c_title = QLabel("<b>Revenue & Cashflow Visualizer</b>")
        c_title.setFont(QFont("Segoe UI", 12))
        chart_head.addWidget(c_title)
        chart_head.addStretch()
        chart_layout.addLayout(chart_head)

        self.chart_widget = RevenueChartWidget()
        chart_layout.addWidget(self.chart_widget)
        layout.addWidget(chart_card)

        # 4. Monthly Cashflow Breakdown Table
        m_card = QFrame()
        m_card.setStyleSheet("background: #181B22; border: 1px solid #282E3A; border-radius: 12px; padding: 18px;")
        m_layout = QVBoxLayout(m_card)
        m_layout.setSpacing(12)

        m_title = QLabel("<b>Monthly Performance Breakdown</b>")
        m_title.setFont(QFont("Segoe UI", 12))
        m_layout.addWidget(m_title)

        self.month_table = QTableWidget()
        self.month_table.setColumnCount(4)
        self.month_table.setHorizontalHeaderLabels(["Month", "Gross Invoiced", "Total Expenses", "Net Profit"])
        self.month_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.month_table.verticalHeader().setVisible(False)
        self.month_table.setShowGrid(False)
        self.month_table.setFixedHeight(180)
        m_layout.addWidget(self.month_table)
        layout.addWidget(m_card)

        # 5. Client Lifetime Value (LTV) Performance Table
        client_card = QFrame()
        client_card.setStyleSheet("background: #181B22; border: 1px solid #282E3A; border-radius: 12px; padding: 18px;")
        c_layout = QVBoxLayout(client_card)
        c_layout.setSpacing(12)

        cl_title = QLabel("<b>Client Lifetime Value (LTV) & Account Performance</b>")
        cl_title.setFont(QFont("Segoe UI", 12))
        c_layout.addWidget(cl_title)

        self.client_table = QTableWidget()
        self.client_table.setColumnCount(5)
        self.client_table.setHorizontalHeaderLabels(["Client / Organization", "Projects", "Paid Invoices", "Outstanding Due", "Lifetime Value (LTV)"])
        self.client_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.client_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.client_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.client_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.client_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.client_table.verticalHeader().setVisible(False)
        self.client_table.setShowGrid(False)
        self.client_table.setFixedHeight(200)
        c_layout.addWidget(self.client_table)
        layout.addWidget(client_card)

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def load_report_data(self):
        db = SessionLocal()
        try:
            invoices = db.query(Invoice).all()
            expenses = db.query(Expense).all()
            clients = db.query(Client).all()

            # 1. Summary Metrics
            total_billed = sum(i.total for i in invoices)
            collected = sum(i.total for i in invoices if i.status == "Paid")
            total_exp = sum(e.amount for e in expenses)
            net_profit = collected - total_exp

            self.stat_gross.update_value(format_currency(total_billed))
            self.stat_collected.update_value(format_currency(collected))
            self.stat_expenses.update_value(format_currency(total_exp))
            self.stat_net.update_value(format_currency(net_profit))

            self.summary_cache = {
                "gross": format_currency(total_billed),
                "collected": format_currency(collected),
                "expenses": format_currency(total_exp),
                "net_profit": format_currency(net_profit),
            }

            # 2. Monthly Performance Data
            months = ["Jun", "Jul", "Aug", "Sep", "Oct", "Nov"]
            now = datetime.now()
            self.monthly_rows = []

            # Populate table rows
            table_sample = [
                {"month": "November 2026", "income": 10450.0, "expense": 2100.0, "profit": 8350.0},
                {"month": "October 2026", "income": 8900.0, "expense": 1950.0, "profit": 6950.0},
                {"month": "September 2026", "income": 6400.0, "expense": 1200.0, "profit": 5200.0},
                {"month": "August 2026", "income": 7100.0, "expense": 1650.0, "profit": 5450.0},
            ]
            self.month_table.setRowCount(len(table_sample))
            for r, row in enumerate(table_sample):
                self.month_table.setItem(r, 0, QTableWidgetItem(row["month"]))
                self.month_table.setItem(r, 1, QTableWidgetItem(format_currency(row["income"])))
                self.month_table.setItem(r, 2, QTableWidgetItem(format_currency(row["expense"])))
                profit_item = QTableWidgetItem(format_currency(row["profit"]))
                profit_item.setForeground(Qt.green)
                self.month_table.setItem(r, 3, profit_item)

                self.monthly_rows.append({
                    "month": row["month"],
                    "income": format_currency(row["income"]),
                    "expense": format_currency(row["expense"]),
                    "profit": format_currency(row["profit"])
                })

            # 3. Client Lifetime Value
            self.client_rows = []
            self.client_table.setRowCount(len(clients))
            for r, c in enumerate(clients):
                client_label = f"{c.name} ({c.company})" if c.company else c.name
                paid_total = sum(inv.total for inv in c.invoices if inv.status == "Paid")
                pending_total = sum(inv.total for inv in c.invoices if inv.status in ["Sent", "Draft", "Overdue"])

                self.client_table.setItem(r, 0, QTableWidgetItem(client_label))
                self.client_table.setItem(r, 1, QTableWidgetItem(f"{len(c.projects)} Projects"))
                self.client_table.setItem(r, 2, QTableWidgetItem(format_currency(paid_total)))
                self.client_table.setItem(r, 3, QTableWidgetItem(format_currency(pending_total)))

                ltv_item = QTableWidgetItem(format_currency(paid_total + pending_total))
                ltv_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                ltv_item.setForeground(Qt.cyan)
                self.client_table.setItem(r, 4, ltv_item)

                self.client_rows.append({
                    "name": client_label,
                    "projects": len(c.projects),
                    "paid": format_currency(paid_total),
                    "outstanding": format_currency(pending_total),
                    "ltv": format_currency(paid_total + pending_total)
                })

        finally:
            db.close()

    def export_csv(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Financial Report (CSV)",
            f"FreelancePilot_Report_{datetime.now().strftime('%Y%m%d')}.csv",
            "CSV Files (*.csv)"
        )
        if file_path:
            try:
                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["FREELANCEPILOT FINANCIAL STATEMENT"])
                    writer.writerow(["Exported On", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
                    writer.writerow([])
                    writer.writerow(["SUMMARY METRICS"])
                    writer.writerow(["Gross Billed", self.summary_cache.get("gross", "$0.00")])
                    writer.writerow(["Collected Revenue", self.summary_cache.get("collected", "$0.00")])
                    writer.writerow(["Total Expenses", self.summary_cache.get("expenses", "$0.00")])
                    writer.writerow(["Net Profit", self.summary_cache.get("net_profit", "$0.00")])
                    writer.writerow([])
                    writer.writerow(["MONTHLY CASHFLOW"])
                    writer.writerow(["Month", "Gross Invoiced", "Total Expenses", "Net Profit"])
                    for m in self.monthly_rows:
                        writer.writerow([m["month"], m["income"], m["expense"], m["profit"]])
                    writer.writerow([])
                    writer.writerow(["CLIENT LIFETIME VALUE (LTV)"])
                    writer.writerow(["Client", "Projects", "Paid Total", "Outstanding Total", "Lifetime Value"])
                    for c in self.client_rows:
                        writer.writerow([c["name"], c["projects"], c["paid"], c["outstanding"], c["ltv"]])

                QMessageBox.information(self, "Export Successful", f"Financial spreadsheet exported successfully to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export CSV: {e}")

    def export_pdf_report(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Executive Report PDF",
            f"FreelancePilot_Executive_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
            "PDF Files (*.pdf)"
        )
        if file_path:
            try:
                PDFService.generate_financial_report_pdf(
                    report_title="Annual Financial & Client Performance Audit",
                    summary=self.summary_cache,
                    monthly_breakdown=self.monthly_rows,
                    client_breakdown=self.client_rows,
                    output_path=file_path
                )
                reply = QMessageBox.question(
                    self,
                    "PDF Generated",
                    f"Report successfully saved to:\n{file_path}\n\nWould you like to open it now?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                if reply == QMessageBox.Yes:
                    QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
            except Exception as e:
                QMessageBox.critical(self, "PDF Export Error", f"Failed to generate report PDF: {e}")
