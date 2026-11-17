"""
Main Application Window for FreelancePilot.
Integrates the Collapsible Sidebar, Topbar, and QStackedWidget workspaces.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget, QApplication, QDialog
)
from PySide6.QtCore import Qt
import qtawesome as qta

from components.sidebar import Sidebar
from components.topbar import Topbar
from components.dialogs import ProjectDialog, InvoiceDialog
from assets.styles.theme import get_stylesheet
from ui.dashboard import DashboardView
from ui.clients import ClientsView
from ui.projects import ProjectsView
from ui.tasks import TasksView
from ui.invoices import InvoicesView
from ui.expenses import ExpensesView
from ui.ai_assistant import AIAssistantView
from ui.proposal_generator import ProposalGeneratorView
from ui.seo_studio import SEOStudioView
from ui.templates import TemplatesView
from ui.reports import ReportsView
from ui.settings import SettingsView


class MainWindow(QMainWindow):
    """
    FreelancePilot Primary Window.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FreelancePilot – AI Business Assistant")
        self.setWindowIcon(qta.icon("fa5s.paper-plane", color="#2563EB"))
        self.resize(1300, 850)
        self.setMinimumSize(1024, 700)

        self.current_theme = "dark"
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)

        # Main horizontal layout: [Sidebar] + [Right Work Area: Topbar + Pages]
        app_layout = QHBoxLayout(central_widget)
        app_layout.setContentsMargins(0, 0, 0, 0)
        app_layout.setSpacing(0)

        # 1. Left Sidebar
        self.sidebar = Sidebar(self)
        self.sidebar.nav_changed.connect(self.switch_page)
        app_layout.addWidget(self.sidebar)

        # 2. Right Work Area
        work_area = QWidget()
        work_area_layout = QVBoxLayout(work_area)
        work_area_layout.setContentsMargins(0, 0, 0, 0)
        work_area_layout.setSpacing(0)

        # Top Bar
        self.topbar = Topbar(self)
        self.topbar.theme_toggled.connect(self.toggle_theme)
        self.topbar.ai_shortcut_clicked.connect(lambda: self.switch_page("ai_assistant"))
        self.topbar.new_invoice_clicked.connect(self.open_new_invoice_dialog)
        self.topbar.new_project_clicked.connect(self.open_new_project_dialog)
        self.topbar.search_triggered.connect(self.on_global_search)
        work_area_layout.addWidget(self.topbar)

        # Pages Stack
        self.stack = QStackedWidget()
        self.pages = {}

        # 1. Dashboard View
        self.dashboard_view = DashboardView(self)
        self.dashboard_view.navigate_to.connect(self.switch_page)
        self._add_page("dashboard", self.dashboard_view)

        # 2. Clients View
        self.clients_view = ClientsView(self)
        self.clients_view.data_changed.connect(self.dashboard_view.load_data)
        self._add_page("clients", self.clients_view)

        # 3. Projects View
        self.projects_view = ProjectsView(self)
        self.projects_view.data_changed.connect(self.dashboard_view.load_data)
        self.projects_view.data_changed.connect(self.clients_view.load_clients)
        self._add_page("projects", self.projects_view)

        # 4. Tasks View
        self.tasks_view = TasksView(self)
        self.tasks_view.data_changed.connect(self.dashboard_view.load_data)
        self.tasks_view.data_changed.connect(self.projects_view.load_projects)
        self._add_page("tasks", self.tasks_view)

        # 5. Invoices View
        self.invoices_view = InvoicesView(self)
        self.invoices_view.data_changed.connect(self.dashboard_view.load_data)
        self.invoices_view.data_changed.connect(self.clients_view.load_clients)
        self._add_page("invoices", self.invoices_view)

        # 6. Expenses View
        self.expenses_view = ExpensesView(self)
        self.expenses_view.data_changed.connect(self.dashboard_view.load_data)
        self._add_page("expenses", self.expenses_view)

        # 7. AI Writing Tools
        self._add_page("ai_assistant", AIAssistantView(self))
        self._add_page("proposal_gen", ProposalGeneratorView(self))
        self._add_page("seo_studio", SEOStudioView(self))
        self._add_page("templates", TemplatesView(self))
        self._add_page("reports", ReportsView(self))

        # 8. Settings View
        self.settings_view = SettingsView(self)
        self.settings_view.theme_changed.connect(self.set_theme)
        self._add_page("settings", self.settings_view)

        work_area_layout.addWidget(self.stack, 1)
        app_layout.addWidget(work_area, 1)

    def _add_page(self, key: str, widget: QWidget):
        self.pages[key] = widget
        self.stack.addWidget(widget)

    def switch_page(self, key: str):
        if key in self.pages:
            self.stack.setCurrentWidget(self.pages[key])
            self.sidebar.set_active(key)

    def open_new_project_dialog(self):
        diag = ProjectDialog(parent=self)
        if diag.exec() == QDialog.Accepted:
            self.projects_view.load_projects()
            self.dashboard_view.load_data()

    def open_new_invoice_dialog(self):
        diag = InvoiceDialog(parent=self)
        if diag.exec() == QDialog.Accepted:
            self.invoices_view.load_invoices()
            self.dashboard_view.load_data()

    def on_global_search(self, query: str):
        current_widget = self.stack.currentWidget()
        if current_widget == self.clients_view:
            self.clients_view.search_box.setText(query)
        elif current_widget == self.projects_view:
            self.projects_view.search_box.setText(query)
        elif current_widget == self.tasks_view:
            self.tasks_view.search_box.setText(query)
        elif current_widget == self.invoices_view:
            self.invoices_view.search_box.setText(query)
        elif current_widget == self.expenses_view:
            self.expenses_view.search_box.setText(query)

    def toggle_theme(self):
        new_theme = "light" if self.current_theme == "dark" else "dark"
        self.set_theme(new_theme)
        self.show_toast(f"Switched to {new_theme.capitalize()} theme", "info")

    def show_toast(self, message: str, toast_type: str = "success"):
        """Displays an animated floating toast notification in the top-right."""
        from components.notifications import ToastNotification
        toast = ToastNotification(message, toast_type, parent=self)
        toast.move(self.width() - 320, 75)
        toast.show()

    def set_theme(self, theme_name: str):
        self.current_theme = theme_name
        app = QApplication.instance()
        if app:
            app.setStyleSheet(get_stylesheet(theme_name))
