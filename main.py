"""
FreelancePilot – AI Business Assistant for Freelancers
Main Application Entry Point.
"""

import sys
import os
import ctypes
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon

# Ensure current directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import init_db
from assets.styles.theme import get_stylesheet
from ui.main_window import MainWindow


def main():
    # Set Windows AppUserModelID so taskbar displays the custom icon
    try:
        myappid = "FreelancePilot.AIAssistant.Desktop.1.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    # 1. Initialize local SQLite Database & seed data
    print("Initializing FreelancePilot Database...")
    init_db()

    # 2. Setup Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("FreelancePilot")
    app.setOrganizationName("FreelancePilot")

    # Set icon
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "icons", "app_icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Set Default modern typography
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # 3. Apply Premium Dark Theme Stylesheet
    app.setStyleSheet(get_stylesheet("dark"))

    # 4. Launch Main Window
    window = MainWindow()
    window.show()

    # 5. Start Qt Event Loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
