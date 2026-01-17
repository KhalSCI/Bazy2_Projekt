"""
Form validation helpers for the Streamlit app.
"""

import re
from typing import Optional, Tuple


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email format.
    Returns (is_valid, error_message)
    """
    if not email:
        return False, "Email jest wymagany"

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Nieprawidłowy format adresu email"

    return True, ""


def validate_login(login: str) -> Tuple[bool, str]:
    """
    Validate login/username.
    Returns (is_valid, error_message)
    """
    if not login:
        return False, "Login jest wymagany"

    if len(login) < 3:
        return False, "Login musi mieć co najmniej 3 znaki"

    if len(login) > 50:
        return False, "Login może mieć maksymalnie 50 znaków"

    if not re.match(r'^[a-zA-Z0-9_]+$', login):
        return False, "Login może zawierać tylko litery, cyfry i podkreślenia"

    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validate password.
    Returns (is_valid, error_message)
    """
    if not password:
        return False, "Hasło jest wymagane"

    if len(password) < 4:
        return False, "Hasło musi mieć co najmniej 4 znaki"

    return True, ""


def validate_positive_number(value: float, field_name: str = "Wartość") -> Tuple[bool, str]:
    """
    Validate that a number is positive.
    Returns (is_valid, error_message)
    """
    if value is None:
        return False, f"{field_name} jest wymagana"

    if value <= 0:
        return False, f"{field_name} musi być większa od zera"

    return True, ""


def validate_quantity(quantity: float, max_quantity: float = None) -> Tuple[bool, str]:
    """
    Validate stock quantity.
    Returns (is_valid, error_message)
    """
    if quantity is None:
        return False, "Ilość jest wymagana"

    if quantity <= 0:
        return False, "Ilość musi być większa od zera"

    if max_quantity is not None and quantity > max_quantity:
        return False, f"Ilość nie może przekraczać {max_quantity}"

    return True, ""


def validate_currency(currency: str) -> Tuple[bool, str]:
    """
    Validate currency code.
    Returns (is_valid, error_message)
    """
    if not currency:
        return False, "Waluta jest wymagana"

    if len(currency) != 3:
        return False, "Kod waluty musi mieć 3 znaki (np. USD, PLN)"

    if not currency.isalpha():
        return False, "Kod waluty może zawierać tylko litery"

    return True, ""


def validate_symbol(symbol: str) -> Tuple[bool, str]:
    """
    Validate stock symbol.
    Returns (is_valid, error_message)
    """
    if not symbol:
        return False, "Symbol jest wymagany"

    if len(symbol) > 20:
        return False, "Symbol może mieć maksymalnie 20 znaków"

    if not re.match(r'^[A-Za-z0-9.]+$', symbol):
        return False, "Symbol może zawierać tylko litery, cyfry i kropki"

    return True, ""


def validate_name(name: str, field_name: str = "Nazwa",
                  min_length: int = 1, max_length: int = 100) -> Tuple[bool, str]:
    """
    Validate a name field.
    Returns (is_valid, error_message)
    """
    if not name:
        return False, f"{field_name} jest wymagana"

    if len(name) < min_length:
        return False, f"{field_name} musi mieć co najmniej {min_length} znaków"

    if len(name) > max_length:
        return False, f"{field_name} może mieć maksymalnie {max_length} znaków"

    return True, ""


def validate_sufficient_funds(required: float, available: float,
                              currency: str = "USD") -> Tuple[bool, str]:
    """
    Validate that there are sufficient funds for a transaction.
    Returns (is_valid, error_message)
    """
    if required > available:
        return False, f"Niewystarczające środki. Wymagane: {required:.2f} {currency}, dostępne: {available:.2f} {currency}"

    return True, ""


def validate_sufficient_shares(required: float, owned: float,
                               symbol: str = "") -> Tuple[bool, str]:
    """
    Validate that there are sufficient shares for a sale.
    Returns (is_valid, error_message)
    """
    if required > owned:
        symbol_info = f" ({symbol})" if symbol else ""
        return False, f"Niewystarczająca ilość akcji{symbol_info}. Posiadasz: {owned:.4f}"

    return True, ""


def format_currency(value: float, currency: str = "USD") -> str:
    """Format a value as currency."""
    if value is None:
        return "-"
    return f"{value:,.2f} {currency}"


def format_quantity(value: float) -> str:
    """Format a quantity value."""
    if value is None:
        return "-"
    if value == int(value):
        return f"{int(value)}"
    return f"{value:.4f}"


def format_percent(value: float) -> str:
    """Format a percentage value with color indicator."""
    if value is None:
        return "-"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.2f}%"


def format_change(value: float, percent: float = None) -> str:
    """Format a change value with optional percentage."""
    if value is None:
        return "-"

    sign = "+" if value > 0 else ""
    result = f"{sign}{value:.2f}"

    if percent is not None:
        result += f" ({sign}{percent:.2f}%)"

    return result
