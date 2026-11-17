"""
Theme management and QSS stylesheets for FreelancePilot.
Supports Dark mode (default) and Light mode.
"""

from utils.config import DARK_THEME, LIGHT_THEME

CURRENT_THEME = "dark"


def get_stylesheet(theme_name: str = "dark") -> str:
    """Generates the comprehensive QSS stylesheet for the given theme."""
    palette = DARK_THEME if theme_name.lower() == "dark" else LIGHT_THEME

    return f"""
    /* Global Application Styles */
    QMainWindow, QWidget#centralWidget {{
        background-color: {palette["bg_main"]};
        color: {palette["text_primary"]};
        font-family: 'Segoe UI', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 13px;
    }}

    QWidget {{
        color: {palette["text_primary"]};
        outline: none;
    }}

    /* Scrollbars */
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {palette["border_light"]};
        min-height: 24px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {palette["accent_primary"]};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 8px;
        margin: 0px;
    }}
    QScrollBar::handle:horizontal {{
        background: {palette["border_light"]};
        min-width: 24px;
        border-radius: 4px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {palette["accent_primary"]};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    /* Buttons */
    QPushButton {{
        background-color: {palette["bg_surface"]};
        color: {palette["text_primary"]};
        border: 1px solid {palette["border"]};
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 500;
        font-size: 13px;
    }}
    QPushButton:hover {{
        background-color: {palette["bg_card_hover"]};
        border-color: {palette["border_light"]};
    }}
    QPushButton:pressed {{
        background-color: {palette["bg_surface_alt"]};
    }}
    QPushButton:disabled {{
        color: {palette["text_muted"]};
        border-color: {palette["border"]};
        background-color: {palette["bg_main"]};
    }}

    /* Primary Accent Button */
    QPushButton#primaryButton {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {palette["accent_primary"]}, stop:1 {palette["accent_secondary"]});
        color: #FFFFFF;
        border: none;
        border-radius: 8px;
        padding: 8px 18px;
        font-weight: 600;
    }}
    QPushButton#primaryButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {palette["accent_primary_hover"]}, stop:1 {palette["accent_secondary"]});
    }}
    QPushButton#primaryButton:pressed {{
        background-color: {palette["accent_primary"]};
    }}

    /* Secondary / Ghost Button */
    QPushButton#ghostButton {{
        background-color: transparent;
        border: 1px solid transparent;
        color: {palette["text_secondary"]};
    }}
    QPushButton#ghostButton:hover {{
        background-color: {palette["bg_surface"]};
        border-color: {palette["border"]};
        color: {palette["text_primary"]};
    }}

    /* Inputs & LineEdits */
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {palette["bg_surface"]};
        color: {palette["text_primary"]};
        border: 1px solid {palette["border"]};
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 13px;
        selection-background-color: {palette["accent_primary"]};
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border: 1px solid {palette["accent_primary"]};
        background-color: {palette["bg_card"]};
    }}
    QLineEdit:disabled, QTextEdit:disabled {{
        background-color: {palette["bg_main"]};
        color: {palette["text_muted"]};
    }}

    /* ComboBox */
    QComboBox {{
        background-color: {palette["bg_surface"]};
        color: {palette["text_primary"]};
        border: 1px solid {palette["border"]};
        border-radius: 8px;
        padding: 7px 12px;
        font-size: 13px;
        min-height: 20px;
    }}
    QComboBox:hover {{
        border-color: {palette["border_light"]};
    }}
    QComboBox:focus {{
        border: 1px solid {palette["accent_primary"]};
    }}
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 24px;
        border-left-width: 0px;
        border-top-right-radius: 8px;
        border-bottom-right-radius: 8px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {palette["bg_surface"]};
        color: {palette["text_primary"]};
        border: 1px solid {palette["border"]};
        border-radius: 8px;
        selection-background-color: {palette["accent_primary"]};
        selection-color: #FFFFFF;
        padding: 4px;
    }}

    /* Tooltips */
    QToolTip {{
        background-color: {palette["bg_surface_alt"]};
        color: {palette["text_primary"]};
        border: 1px solid {palette["border"]};
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 12px;
    }}

    /* Tables */
    QTableWidget, QTableView {{
        background-color: {palette["bg_card"]};
        gridline-color: {palette["border"]};
        border: 1px solid {palette["border"]};
        border-radius: 10px;
        color: {palette["text_primary"]};
        selection-background-color: {palette["bg_surface_alt"]};
        selection-color: {palette["accent_primary"]};
    }}
    QHeaderView::section {{
        background-color: {palette["bg_surface"]};
        color: {palette["text_secondary"]};
        padding: 8px 12px;
        border: none;
        border-bottom: 1px solid {palette["border"]};
        font-weight: 600;
        font-size: 12px;
    }}

    /* Progress Bar */
    QProgressBar {{
        background-color: {palette["bg_surface_alt"]};
        border: none;
        border-radius: 5px;
        height: 8px;
        text-align: center;
    }}
    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {palette["accent_primary"]}, stop:1 {palette["accent_secondary"]});
        border-radius: 5px;
    }}

    /* Card Frames */
    QFrame#cardFrame {{
        background-color: {palette["bg_card"]};
        border: 1px solid {palette["border"]};
        border-radius: 12px;
    }}
    QFrame#cardFrame:hover {{
        border-color: {palette["border_light"]};
    }}

    /* Sidebar and Topbar Frames */
    QFrame#sidebarFrame {{
        background-color: {palette["bg_surface"]};
        border-right: 1px solid {palette["border"]};
    }}
    QFrame#topbarFrame {{
        background-color: {palette["bg_surface"]};
        border-bottom: 1px solid {palette["border"]};
    }}
    """
