"""
Unit tests for validators module.
These tests do not require database connection.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.validators import (
    validate_email,
    validate_login,
    validate_password,
    validate_positive_number,
    validate_quantity,
    validate_currency,
    validate_symbol,
    validate_name,
    validate_sufficient_funds,
    validate_sufficient_shares,
    format_currency,
    format_quantity,
    format_percent,
    format_change
)


class TestValidateEmail:
    """Tests for email validation."""

    def test_valid_email(self):
        """Test valid email addresses."""
        valid_emails = [
            'test@example.com',
            'user.name@domain.org',
            'user+tag@example.co.uk',
            'user123@test-domain.com'
        ]
        for email in valid_emails:
            is_valid, msg = validate_email(email)
            assert is_valid, f"Email {email} should be valid, got: {msg}"

    def test_invalid_email_empty(self):
        """Test empty email."""
        is_valid, msg = validate_email('')
        assert not is_valid
        assert 'wymagany' in msg.lower()

    def test_invalid_email_no_at(self):
        """Test email without @ symbol."""
        is_valid, msg = validate_email('testexample.com')
        assert not is_valid
        assert 'format' in msg.lower()

    def test_invalid_email_no_domain(self):
        """Test email without domain."""
        is_valid, msg = validate_email('test@')
        assert not is_valid

    def test_invalid_email_no_tld(self):
        """Test email without TLD."""
        is_valid, msg = validate_email('test@example')
        assert not is_valid


class TestValidateLogin:
    """Tests for login validation."""

    def test_valid_login(self):
        """Test valid logins."""
        valid_logins = ['user', 'user123', 'User_Name', 'a' * 50]
        for login in valid_logins:
            is_valid, msg = validate_login(login)
            assert is_valid, f"Login {login} should be valid, got: {msg}"

    def test_invalid_login_empty(self):
        """Test empty login."""
        is_valid, msg = validate_login('')
        assert not is_valid
        assert 'wymagany' in msg.lower()

    def test_invalid_login_too_short(self):
        """Test login too short."""
        is_valid, msg = validate_login('ab')
        assert not is_valid
        assert '3' in msg

    def test_invalid_login_too_long(self):
        """Test login too long."""
        is_valid, msg = validate_login('a' * 51)
        assert not is_valid
        assert '50' in msg

    def test_invalid_login_special_chars(self):
        """Test login with special characters."""
        invalid_logins = ['user@name', 'user name', 'user!123', 'użytkownik']
        for login in invalid_logins:
            is_valid, msg = validate_login(login)
            assert not is_valid, f"Login {login} should be invalid"


class TestValidatePassword:
    """Tests for password validation."""

    def test_valid_password(self):
        """Test valid passwords."""
        valid_passwords = ['1234', 'password', 'P@ssw0rd!', 'a' * 100]
        for password in valid_passwords:
            is_valid, msg = validate_password(password)
            assert is_valid, f"Password should be valid, got: {msg}"

    def test_invalid_password_empty(self):
        """Test empty password."""
        is_valid, msg = validate_password('')
        assert not is_valid
        assert 'wymagane' in msg.lower()

    def test_invalid_password_too_short(self):
        """Test password too short."""
        is_valid, msg = validate_password('123')
        assert not is_valid
        assert '4' in msg


class TestValidatePositiveNumber:
    """Tests for positive number validation."""

    def test_valid_positive_numbers(self):
        """Test valid positive numbers."""
        valid_numbers = [1, 0.01, 100.50, 1000000]
        for num in valid_numbers:
            is_valid, msg = validate_positive_number(num)
            assert is_valid, f"Number {num} should be valid, got: {msg}"

    def test_invalid_number_none(self):
        """Test None value."""
        is_valid, msg = validate_positive_number(None)
        assert not is_valid
        assert 'wymagana' in msg.lower()

    def test_invalid_number_zero(self):
        """Test zero value."""
        is_valid, msg = validate_positive_number(0)
        assert not is_valid
        assert 'większa od zera' in msg.lower()

    def test_invalid_number_negative(self):
        """Test negative value."""
        is_valid, msg = validate_positive_number(-10)
        assert not is_valid
        assert 'większa od zera' in msg.lower()

    def test_custom_field_name(self):
        """Test custom field name in error message."""
        is_valid, msg = validate_positive_number(None, "Cena")
        assert not is_valid
        assert 'Cena' in msg


class TestValidateQuantity:
    """Tests for quantity validation."""

    def test_valid_quantity(self):
        """Test valid quantities."""
        is_valid, msg = validate_quantity(10)
        assert is_valid

    def test_valid_quantity_fractional(self):
        """Test valid fractional quantity."""
        is_valid, msg = validate_quantity(0.5)
        assert is_valid

    def test_valid_quantity_with_max(self):
        """Test quantity within max limit."""
        is_valid, msg = validate_quantity(5, max_quantity=10)
        assert is_valid

    def test_invalid_quantity_none(self):
        """Test None quantity."""
        is_valid, msg = validate_quantity(None)
        assert not is_valid
        assert 'wymagana' in msg.lower()

    def test_invalid_quantity_zero(self):
        """Test zero quantity."""
        is_valid, msg = validate_quantity(0)
        assert not is_valid

    def test_invalid_quantity_negative(self):
        """Test negative quantity."""
        is_valid, msg = validate_quantity(-5)
        assert not is_valid

    def test_invalid_quantity_exceeds_max(self):
        """Test quantity exceeding max."""
        is_valid, msg = validate_quantity(15, max_quantity=10)
        assert not is_valid
        assert '10' in msg


class TestValidateCurrency:
    """Tests for currency validation."""

    def test_valid_currencies(self):
        """Test valid currency codes."""
        valid_currencies = ['USD', 'PLN', 'EUR', 'GBP', 'CHF', 'JPY']
        for currency in valid_currencies:
            is_valid, msg = validate_currency(currency)
            assert is_valid, f"Currency {currency} should be valid, got: {msg}"

    def test_invalid_currency_empty(self):
        """Test empty currency."""
        is_valid, msg = validate_currency('')
        assert not is_valid
        assert 'wymagana' in msg.lower()

    def test_invalid_currency_wrong_length(self):
        """Test currency with wrong length."""
        is_valid, msg = validate_currency('US')
        assert not is_valid
        assert '3' in msg

        is_valid, msg = validate_currency('USDD')
        assert not is_valid
        assert '3' in msg

    def test_invalid_currency_with_numbers(self):
        """Test currency with numbers."""
        is_valid, msg = validate_currency('US1')
        assert not is_valid
        assert 'litery' in msg.lower()


class TestValidateSymbol:
    """Tests for stock symbol validation."""

    def test_valid_symbols(self):
        """Test valid stock symbols."""
        valid_symbols = ['AAPL', 'MSFT', 'GOOGL', 'BRK.A', 'BRK.B']
        for symbol in valid_symbols:
            is_valid, msg = validate_symbol(symbol)
            assert is_valid, f"Symbol {symbol} should be valid, got: {msg}"

    def test_invalid_symbol_empty(self):
        """Test empty symbol."""
        is_valid, msg = validate_symbol('')
        assert not is_valid
        assert 'wymagany' in msg.lower()

    def test_invalid_symbol_too_long(self):
        """Test symbol too long."""
        is_valid, msg = validate_symbol('A' * 21)
        assert not is_valid
        assert '20' in msg

    def test_invalid_symbol_special_chars(self):
        """Test symbol with invalid characters."""
        is_valid, msg = validate_symbol('AAPL@')
        assert not is_valid


class TestValidateName:
    """Tests for name validation."""

    def test_valid_name(self):
        """Test valid names."""
        is_valid, msg = validate_name('Portfel główny')
        assert is_valid

    def test_invalid_name_empty(self):
        """Test empty name."""
        is_valid, msg = validate_name('')
        assert not is_valid
        assert 'wymagana' in msg.lower()

    def test_invalid_name_too_short(self):
        """Test name too short."""
        is_valid, msg = validate_name('', min_length=3)
        assert not is_valid

    def test_invalid_name_too_long(self):
        """Test name too long."""
        is_valid, msg = validate_name('A' * 101, max_length=100)
        assert not is_valid
        assert '100' in msg

    def test_custom_field_name(self):
        """Test custom field name."""
        is_valid, msg = validate_name('', field_name='Tytuł')
        assert not is_valid
        assert 'Tytuł' in msg


class TestValidateSufficientFunds:
    """Tests for sufficient funds validation."""

    def test_sufficient_funds(self):
        """Test when funds are sufficient."""
        is_valid, msg = validate_sufficient_funds(100, 200)
        assert is_valid

    def test_sufficient_funds_equal(self):
        """Test when funds are exactly equal."""
        is_valid, msg = validate_sufficient_funds(100, 100)
        assert is_valid

    def test_insufficient_funds(self):
        """Test when funds are insufficient."""
        is_valid, msg = validate_sufficient_funds(200, 100)
        assert not is_valid
        assert 'Niewystarczające' in msg
        assert '200.00' in msg
        assert '100.00' in msg

    def test_custom_currency(self):
        """Test with custom currency."""
        is_valid, msg = validate_sufficient_funds(200, 100, 'PLN')
        assert not is_valid
        assert 'PLN' in msg


class TestValidateSufficientShares:
    """Tests for sufficient shares validation."""

    def test_sufficient_shares(self):
        """Test when shares are sufficient."""
        is_valid, msg = validate_sufficient_shares(5, 10)
        assert is_valid

    def test_sufficient_shares_equal(self):
        """Test when shares are exactly equal."""
        is_valid, msg = validate_sufficient_shares(10, 10)
        assert is_valid

    def test_insufficient_shares(self):
        """Test when shares are insufficient."""
        is_valid, msg = validate_sufficient_shares(15, 10)
        assert not is_valid
        assert 'Niewystarczająca' in msg
        assert '10.0000' in msg

    def test_with_symbol(self):
        """Test with symbol in message."""
        is_valid, msg = validate_sufficient_shares(15, 10, 'AAPL')
        assert not is_valid
        assert 'AAPL' in msg


class TestFormatCurrency:
    """Tests for currency formatting."""

    def test_format_positive(self):
        """Test formatting positive value."""
        result = format_currency(1234.56, 'USD')
        assert '1,234.56' in result
        assert 'USD' in result

    def test_format_negative(self):
        """Test formatting negative value."""
        result = format_currency(-500.00, 'PLN')
        assert '-500.00' in result
        assert 'PLN' in result

    def test_format_none(self):
        """Test formatting None value."""
        result = format_currency(None)
        assert result == '-'

    def test_format_zero(self):
        """Test formatting zero."""
        result = format_currency(0, 'EUR')
        assert '0.00' in result
        assert 'EUR' in result


class TestFormatQuantity:
    """Tests for quantity formatting."""

    def test_format_integer(self):
        """Test formatting whole number."""
        result = format_quantity(10.0)
        assert result == '10'

    def test_format_fractional(self):
        """Test formatting fractional number."""
        result = format_quantity(10.5)
        assert result == '10.5000'

    def test_format_none(self):
        """Test formatting None."""
        result = format_quantity(None)
        assert result == '-'


class TestFormatPercent:
    """Tests for percentage formatting."""

    def test_format_positive(self):
        """Test formatting positive percentage."""
        result = format_percent(5.5)
        assert result == '+5.50%'

    def test_format_negative(self):
        """Test formatting negative percentage."""
        result = format_percent(-3.25)
        assert result == '-3.25%'

    def test_format_zero(self):
        """Test formatting zero percentage."""
        result = format_percent(0)
        assert result == '0.00%'

    def test_format_none(self):
        """Test formatting None."""
        result = format_percent(None)
        assert result == '-'


class TestFormatChange:
    """Tests for change value formatting."""

    def test_format_positive_change(self):
        """Test formatting positive change."""
        result = format_change(5.50)
        assert '+5.50' in result

    def test_format_negative_change(self):
        """Test formatting negative change."""
        result = format_change(-3.25)
        assert '-3.25' in result

    def test_format_with_percent(self):
        """Test formatting with percentage."""
        result = format_change(5.50, 2.5)
        assert '+5.50' in result
        assert '+2.50%' in result

    def test_format_none(self):
        """Test formatting None."""
        result = format_change(None)
        assert result == '-'
