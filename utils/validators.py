"""
Input validation utilities for FreelancePilot.
Ensures data integrity before saving to the SQLite database.
"""

import re
from typing import Tuple, Optional


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """Validates email format."""
    email = email.strip() if email else ""
    if not email:
        return False, "Email address is required."

    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(pattern, email):
        return False, "Please enter a valid email address (e.g. name@company.com)."
    return True, None


def validate_non_empty(value: str, field_name: str = "This field") -> Tuple[bool, Optional[str]]:
    """Validates that a string is not empty or whitespace."""
    if not value or not value.strip():
        return False, f"{field_name} cannot be empty."
    return True, None


def validate_amount(value: str, field_name: str = "Amount") -> Tuple[bool, Optional[float], Optional[str]]:
    """Validates that a string can be converted to a positive float."""
    if not value or not str(value).strip():
        return True, 0.0, None  # Allow 0.0 as default

    clean_val = str(value).replace("$", "").replace(",", "").strip()
    try:
        amount = float(clean_val)
        if amount < 0:
            return False, None, f"{field_name} cannot be negative."
        return True, amount, None
    except ValueError:
        return False, None, f"{field_name} must be a valid number."
