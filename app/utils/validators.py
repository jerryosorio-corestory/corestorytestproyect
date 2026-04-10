"""
Input validation utilities used across all service layers.

Keeping validation logic here prevents duplication between routes and services
and makes it easy to unit-test validation rules in isolation.
"""

import re
from datetime import datetime


def validate_isbn(isbn: str) -> bool:
    """
    Validate an ISBN-10 or ISBN-13 string.

    Accepts hyphens and spaces as separators, strips them before checking length.
    Does NOT verify the check digit — that would require network access for lookup.

    Args:
        isbn: Raw ISBN string provided by the caller.

    Returns:
        True if the ISBN has a valid format, False otherwise.
    """
    if not isbn or not isinstance(isbn, str):
        return False

    # Remove common separators to normalise the string
    cleaned = re.sub(r"[\s\-]", "", isbn)

    # ISBN-10: 9 digits followed by a digit or 'X'
    if re.fullmatch(r"\d{9}[\dX]", cleaned):
        return True

    # ISBN-13: exactly 13 digits
    if re.fullmatch(r"\d{13}", cleaned):
        return True

    return False


def validate_email(email: str) -> bool:
    """
    Validate a basic email address format.

    Uses a simple regex — sufficient for input sanitation without external libs.

    Args:
        email: Email string to validate.

    Returns:
        True if the format looks like a valid email, False otherwise.
    """
    if not email or not isinstance(email, str):
        return False

    pattern = r"^[a-zA-Z0-9_.+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9.\-]+$"
    return bool(re.match(pattern, email))


def validate_year(year: int) -> bool:
    """
    Validate that a publication year is within a sensible range.

    Books cannot have been published before the printing press (~1450) and
    cannot have a future publication year.

    Args:
        year: Integer year to validate.

    Returns:
        True if the year is plausible, False otherwise.
    """
    if not isinstance(year, int):
        return False

    current_year = datetime.utcnow().year
    return 1450 <= year <= current_year
