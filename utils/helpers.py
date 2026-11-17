"""
Helper and utility functions for FreelancePilot.
"""

from datetime import datetime


def format_currency(amount: float, currency: str = "USD", symbol: str = "$") -> str:
    """Formats a float as currency string with commas and 2 decimals."""
    if amount is None:
        amount = 0.0
    return f"{symbol}{amount:,.2f}"


def format_date(dt: datetime, format_str: str = "%b %d, %Y") -> str:
    """Formats a datetime object to readable date."""
    if not dt:
        return ""
    return dt.strftime(format_str)


def get_relative_date_string(dt: datetime) -> str:
    """Returns human friendly time differences like 'In 2 days' or 'Yesterday'."""
    if not dt:
        return ""
    now = datetime.now()
    diff = (dt.date() - now.date()).days

    if diff == 0:
        return "Today"
    elif diff == 1:
        return "Tomorrow"
    elif diff == -1:
        return "Yesterday"
    elif diff > 1:
        return f"In {diff} days"
    else:
        return f"{abs(diff)} days ago"
