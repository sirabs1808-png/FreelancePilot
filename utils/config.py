"""
Configuration settings for FreelancePilot.
"""

import os
from pathlib import Path

# Application Metadata
APP_NAME = "FreelancePilot"
APP_VERSION = "1.0.0"
APP_TAGLINE = "AI Business Assistant for Freelancers"

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path.home() / ".freelancepilot"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "freelancepilot.db"
BACKUP_DIR = DATA_DIR / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR = DATA_DIR / "exports"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Theme Palette Constants
DARK_THEME = {
    "bg_main": "#0D0F12",
    "bg_surface": "#16191E",
    "bg_surface_alt": "#1D2128",
    "bg_card": "#181B22",
    "bg_card_hover": "#20252F",
    "border": "#282E3A",
    "border_light": "#363E4E",
    "accent_primary": "#2563EB",       # Electric Blue
    "accent_primary_hover": "#3B82F6",
    "accent_secondary": "#7C3AED",     # Modern Violet
    "accent_gradient_start": "#2563EB",
    "accent_gradient_end": "#7C3AED",
    "text_primary": "#F8FAFC",
    "text_secondary": "#94A3B8",
    "text_muted": "#64748B",
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "info": "#06B6D4",
}

LIGHT_THEME = {
    "bg_main": "#F8FAFC",
    "bg_surface": "#FFFFFF",
    "bg_surface_alt": "#F1F5F9",
    "bg_card": "#FFFFFF",
    "bg_card_hover": "#F8FAFC",
    "border": "#E2E8F0",
    "border_light": "#CBD5E1",
    "accent_primary": "#2563EB",
    "accent_primary_hover": "#1D4ED8",
    "accent_secondary": "#7C3AED",
    "accent_gradient_start": "#2563EB",
    "accent_gradient_end": "#7C3AED",
    "text_primary": "#0F172A",
    "text_secondary": "#475569",
    "text_muted": "#94A3B8",
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "info": "#06B6D4",
}
