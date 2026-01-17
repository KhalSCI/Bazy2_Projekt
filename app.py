"""
Symulator Giełdy - Main Streamlit Application

Polish-language stock exchange simulation for educational purposes.
"""

import streamlit as st
from datetime import date, datetime
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import APP_CONFIG, SUPPORTED_CURRENCIES
from services.portfolio_service import UserService, PortfolioService
from services.market_service import MarketService
from services.data_loader import DataLoader
from db.connection import test_connection


def init_session_state():
    """Initialize session state variables."""
    defaults = {
        'user_id': None,
        'user_data': None,
        'portfolio_id': None,
        'portfolio_data': None,
        'simulation_date': date.today(),
        'is_time_travel': False,
        'logged_in': False,
        'show_login': True,
        'show_register': False,
        'db_initialized': False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def check_database():
    """Check database connection and initialization status."""
    success, message = test_connection()
    if not success:
        st.error(f"Błąd połączenia z bazą danych: {message}")
        st.info("Sprawdź ustawienia połączenia w config.py")
        return False

    # Check data status
    status = DataLoader.check_data_status()

    if not status.get('is_initialized', False):
        st.warning("Baza danych wymaga inicjalizacji.")
        if st.button("Inicjalizuj bazę danych"):
            with st.spinner("Inicjalizacja bazy danych..."):
                progress_placeholder = st.empty()

                def progress_callback(step, message):
                    progress_placeholder.info(f"Krok {step}/5: {message}")

                success, messages = DataLoader.initialize_all(progress_callback)

                if success:
                    st.success("Baza danych została zainicjalizowana!")
                    for msg in messages:
                        st.info(msg)
                    st.rerun()
                else:
                    st.error("Błąd podczas inicjalizacji bazy danych")
                    for msg in messages:
                        st.error(msg)
        return False

    st.session_state.db_initialized = True
    return True


def login_form():
    """Display login form."""
    st.subheader("Logowanie")

    with st.form("login_form"):
        login = st.text_input("Login")
        password = st.text_input("Hasło", type="password")
        submit = st.form_submit_button("Zaloguj się")

        if submit:
            if not login or not password:
                st.error("Wprowadź login i hasło")
            else:
                success, message, user_data = UserService.authenticate(login, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user_data['user_id']
                    st.session_state.user_data = user_data

                    # Get user's portfolios
                    portfolios = PortfolioService.get_user_portfolios(user_data['user_id'])
                    if portfolios:
                        st.session_state.portfolio_id = portfolios[0]['portfolio_id']
                        st.session_state.portfolio_data = portfolios[0]

                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

    if st.button("Nie masz konta? Zarejestruj się"):
        st.session_state.show_login = False
        st.session_state.show_register = True
        st.rerun()


def register_form():
    """Display registration form."""
    st.subheader("Rejestracja")

    with st.form("register_form"):
        login = st.text_input("Login")
        email = st.text_input("Email")
        password = st.text_input("Hasło", type="password")
        password_confirm = st.text_input("Potwierdź hasło", type="password")
        first_name = st.text_input("Imię (opcjonalnie)")
        last_name = st.text_input("Nazwisko (opcjonalnie)")

        col1, col2 = st.columns(2)
        with col1:
            portfolio_name = st.text_input("Nazwa portfela", value="Mój portfel")
        with col2:
            portfolio_currency = st.selectbox("Waluta portfela", SUPPORTED_CURRENCIES)

        initial_balance = st.number_input(
            "Saldo początkowe",
            min_value=0.0,
            value=10000.0,
            step=1000.0,
            help="Kwota wirtualnych środków na start"
        )

        submit = st.form_submit_button("Zarejestruj się")

        if submit:
            # Validation
            from utils.validators import validate_login, validate_email, validate_password

            valid_login, msg = validate_login(login)
            if not valid_login:
                st.error(msg)
            elif not email:
                st.error("Email jest wymagany")
            else:
                valid_email, msg = validate_email(email)
                if not valid_email:
                    st.error(msg)
                elif password != password_confirm:
                    st.error("Hasła nie są zgodne")
                else:
                    valid_pass, msg = validate_password(password)
                    if not valid_pass:
                        st.error(msg)
                    else:
                        # Create user
                        success, message, user_id = UserService.create_user(
                            login, password, email,
                            first_name or None, last_name or None
                        )

                        if success and user_id:
                            # Create portfolio
                            port_success, port_msg, portfolio_id = PortfolioService.create_portfolio(
                                user_id, portfolio_name, portfolio_currency, initial_balance
                            )

                            if port_success:
                                st.success("Konto utworzone pomyślnie! Możesz się teraz zalogować.")
                                st.session_state.show_login = True
                                st.session_state.show_register = False
                                st.rerun()
                            else:
                                st.warning(f"Konto utworzone, ale błąd przy tworzeniu portfela: {port_msg}")
                        else:
                            st.error(message)

    if st.button("Masz już konto? Zaloguj się"):
        st.session_state.show_login = True
        st.session_state.show_register = False
        st.rerun()


def sidebar():
    """Display sidebar with user info and navigation."""
    with st.sidebar:
        st.title("Symulator Giełdy")

        if st.session_state.logged_in and st.session_state.user_data:
            user = st.session_state.user_data
            st.write(f"Zalogowany: **{user.get('login', 'N/A')}**")

            # Portfolio selector
            portfolios = PortfolioService.get_user_portfolios(st.session_state.user_id)

            if portfolios:
                portfolio_options = {p['nazwa_portfela']: p['portfolio_id'] for p in portfolios}
                current_portfolio_name = None
                for name, pid in portfolio_options.items():
                    if pid == st.session_state.portfolio_id:
                        current_portfolio_name = name
                        break

                selected_portfolio = st.selectbox(
                    "Aktywny portfel",
                    options=list(portfolio_options.keys()),
                    index=list(portfolio_options.keys()).index(current_portfolio_name) if current_portfolio_name else 0
                )

                new_portfolio_id = portfolio_options[selected_portfolio]
                if new_portfolio_id != st.session_state.portfolio_id:
                    st.session_state.portfolio_id = new_portfolio_id
                    st.session_state.portfolio_data = next(
                        (p for p in portfolios if p['portfolio_id'] == new_portfolio_id), None
                    )
                    st.rerun()

            st.divider()

            # Time travel feature
            st.subheader("Podróż w czasie")

            # Get available date range
            min_date, max_date = MarketService.get_date_range()

            if min_date and max_date:
                # Convert to date if datetime
                if hasattr(min_date, 'date'):
                    min_date = min_date.date()
                if hasattr(max_date, 'date'):
                    max_date = max_date.date()

                # Ensure simulation_date is within available range
                current_sim_date = st.session_state.simulation_date
                if current_sim_date < min_date or current_sim_date > max_date:
                    current_sim_date = max_date
                    st.session_state.simulation_date = max_date
                    st.session_state.is_time_travel = True

                simulation_date = st.date_input(
                    "Data symulacji",
                    value=current_sim_date,
                    min_value=min_date,
                    max_value=max_date,
                    help="Wybierz datę do symulacji historycznych cen"
                )

                if simulation_date != st.session_state.simulation_date:
                    st.session_state.simulation_date = simulation_date
                    st.session_state.is_time_travel = (simulation_date != date.today())
                    st.rerun()

                if st.session_state.is_time_travel:
                    st.info(f"Tryb historyczny: {st.session_state.simulation_date}")
                    if st.button("Powrót do bieżącej daty"):
                        st.session_state.simulation_date = date.today()
                        st.session_state.is_time_travel = False
                        st.rerun()
            else:
                st.warning("Brak danych cenowych")

            st.divider()

            # Logout button
            if st.button("Wyloguj się"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()


def main():
    """Main application entry point."""
    # Page config
    st.set_page_config(
        page_title=APP_CONFIG['title'],
        page_icon=APP_CONFIG['page_icon'],
        layout=APP_CONFIG['layout'],
        initial_sidebar_state="expanded"
    )

    # Initialize session state
    init_session_state()

    # Check database
    if not check_database():
        return

    # Show login/register if not logged in
    if not st.session_state.logged_in:
        st.title("Symulator Giełdy")
        st.markdown("Edukacyjna aplikacja do nauki inwestowania na giełdzie.")

        if st.session_state.show_register:
            register_form()
        else:
            login_form()
        return

    # Show sidebar for logged in users
    sidebar()

    # Main content - redirect to portfolio page by default
    st.title("Symulator Giełdy")

    if st.session_state.is_time_travel:
        st.warning(f"Tryb historyczny - dane z dnia: {st.session_state.simulation_date}")

    # Show portfolio summary
    if st.session_state.portfolio_id:
        summary = PortfolioService.get_portfolio_summary(st.session_state.portfolio_id)

        if summary:
            col1, col2, col3, col4 = st.columns(4)

            currency = summary.get('waluta_portfela', 'USD')
            saldo = float(summary.get('saldo_gotowkowe', 0) or 0)

            # Calculate values based on time travel mode
            if st.session_state.is_time_travel:
                simulation_date = st.session_state.simulation_date
                positions = PortfolioService.get_positions_for_date(
                    st.session_state.portfolio_id, simulation_date
                )
                wartosc_pozycji = sum(float(p.get('wartosc_biezaca', 0) or 0) for p in positions)
                zysk_strata = sum(float(p.get('zysk_strata', 0) or 0) for p in positions)
                wartosc_calkowita = saldo + wartosc_pozycji
            else:
                wartosc_calkowita = float(summary.get('wartosc_calkowita', 0) or 0)
                wartosc_pozycji = float(summary.get('wartosc_pozycji', 0) or 0)
                zysk_strata = float(summary.get('zysk_strata_pozycji', 0) or 0)

            with col1:
                st.metric(
                    label="Wartość portfela",
                    value=f"{wartosc_calkowita:,.2f} {currency}"
                )

            with col2:
                st.metric(
                    label="Gotówka",
                    value=f"{saldo:,.2f} {currency}"
                )

            with col3:
                st.metric(
                    label="Wartość pozycji",
                    value=f"{wartosc_pozycji:,.2f} {currency}"
                )

            with col4:
                sign = "+" if zysk_strata > 0 else ""
                st.metric(
                    label="Zysk/Strata",
                    value=f"{sign}{zysk_strata:,.2f} {currency}",
                    delta_color="normal" if zysk_strata >= 0 else "inverse"
                )

    st.divider()

    st.markdown("""
    ### Nawigacja

    Użyj menu po lewej stronie, aby przejść do poszczególnych sekcji:

    - **Portfel** - Przegląd portfela i pozycji
    - **Kupno** - Składanie zleceń kupna
    - **Sprzedaż** - Składanie zleceń sprzedaży
    - **Rynek** - Przegląd notowań giełdowych
    - **Historia** - Historia zleceń i transakcji
    - **Ustawienia** - Zarządzanie kontem i portfelami
    """)


if __name__ == "__main__":
    main()
