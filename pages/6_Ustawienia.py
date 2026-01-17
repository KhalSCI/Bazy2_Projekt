"""
Settings page - User settings and portfolio management.
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.portfolio_service import PortfolioService, UserService
from services.data_loader import DataLoader
from db.connection import test_connection
from config import APP_CONFIG
from utils.validators import validate_positive_number


def check_login():
    """Check if user is logged in."""
    if not st.session_state.get('logged_in', False):
        st.warning("Musisz się zalogować, aby zobaczyć tę stronę.")
        st.stop()


def main():
    st.set_page_config(
        page_title="Ustawienia - Symulator Giełdy",
        page_icon=APP_CONFIG['page_icon'],
        layout=APP_CONFIG['layout']
    )

    check_login()

    st.title("Ustawienia")

    user_id = st.session_state.user_id
    user_data = st.session_state.user_data

    # Tabs for different settings
    tab1, tab2, tab3, tab4 = st.tabs([
        "Profil",
        "Portfele",
        "Wpłaty/Wypłaty",
        "System"
    ])

    with tab1:
        st.subheader("Profil użytkownika")

        if user_data:
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Login:** {user_data.get('login', 'N/A')}")
                st.write(f"**Email:** {user_data.get('email', 'N/A')}")

            with col2:
                imie = user_data.get('imie', '')
                nazwisko = user_data.get('nazwisko', '')
                if imie or nazwisko:
                    st.write(f"**Imię i nazwisko:** {imie} {nazwisko}")

                data_rejestracji = user_data.get('data_rejestracji')
                if data_rejestracji:
                    st.write(f"**Data rejestracji:** {data_rejestracji}")

            st.divider()

            # Account statistics
            st.subheader("Statystyki konta")

            portfolios = PortfolioService.get_user_portfolios(user_id)

            total_value = 0
            for p in portfolios:
                value = PortfolioService.get_portfolio_value(p['portfolio_id'])
                total_value += value if value else 0

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Liczba portfeli", len(portfolios))

            with col2:
                st.metric("Łączna wartość", f"{total_value:,.2f} USD")

            with col3:
                total_positions = 0
                for p in portfolios:
                    positions = PortfolioService.get_positions(p['portfolio_id'])
                    total_positions += len(positions)
                st.metric("Łączna liczba pozycji", total_positions)

    with tab2:
        st.subheader("Zarządzanie portfelami")

        # List existing portfolios
        portfolios = PortfolioService.get_user_portfolios(user_id)

        if portfolios:
            st.markdown("**Twoje portfele:**")

            for portfolio in portfolios:
                portfolio_id = portfolio.get('portfolio_id')
                nazwa = portfolio.get('nazwa_portfela', 'N/A')
                waluta = portfolio.get('waluta_portfela', 'USD')
                saldo = float(portfolio.get('saldo_gotowkowe', 0) or 0)
                data_utworzenia = portfolio.get('data_utworzenia')

                is_active = portfolio_id == st.session_state.portfolio_id

                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

                    with col1:
                        prefix = "✅ " if is_active else ""
                        st.markdown(f"**{prefix}{nazwa}**")
                        if data_utworzenia:
                            st.caption(f"Utworzono: {data_utworzenia}")

                    with col2:
                        st.write(f"Waluta: {waluta}")

                    with col3:
                        st.write(f"Saldo: {saldo:,.2f} {waluta}")

                    with col4:
                        if not is_active:
                            if st.button("Wybierz", key=f"select_{portfolio_id}"):
                                st.session_state.portfolio_id = portfolio_id
                                st.session_state.portfolio_data = portfolio
                                st.success(f"Wybrano portfel: {nazwa}")
                                st.rerun()

                    st.divider()

        # Create new portfolio
        st.subheader("Utwórz nowy portfel")

        with st.form("new_portfolio_form"):
            portfolio_name = st.text_input("Nazwa portfela")
            portfolio_currency = 'USD'

            initial_balance = st.number_input(
                "Saldo początkowe",
                min_value=0.0,
                value=10000.0,
                step=1000.0
            )

            submit = st.form_submit_button("Utwórz portfel")

            if submit:
                if not portfolio_name:
                    st.error("Nazwa portfela jest wymagana")
                else:
                    success, message, new_portfolio_id = PortfolioService.create_portfolio(
                        user_id, portfolio_name, portfolio_currency, initial_balance
                    )

                    if success:
                        st.success(f"Portfel '{portfolio_name}' utworzony!")

                        # Optionally set as active
                        if st.checkbox("Ustaw jako aktywny"):
                            st.session_state.portfolio_id = new_portfolio_id
                            st.session_state.portfolio_data = PortfolioService.get_portfolio(new_portfolio_id)

                        st.rerun()
                    else:
                        st.error(f"Błąd: {message}")

    with tab3:
        st.subheader("Wpłaty i wypłaty")

        if not st.session_state.portfolio_id:
            st.warning("Wybierz portfel, aby wykonać operację")
        else:
            portfolio = PortfolioService.get_portfolio(st.session_state.portfolio_id)
            currency = portfolio.get('waluta_portfela', 'USD')
            current_balance = float(portfolio.get('saldo_gotowkowe', 0) or 0)

            st.info(f"Aktualne saldo: **{current_balance:,.2f} {currency}**")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Wpłata środków**")

                with st.form("deposit_form"):
                    deposit_amount = st.number_input(
                        "Kwota wpłaty",
                        min_value=0.01,
                        value=1000.0,
                        step=100.0,
                        key="deposit_amount"
                    )

                    if st.form_submit_button("Wpłać"):
                        valid, msg = validate_positive_number(deposit_amount, "Kwota")
                        if not valid:
                            st.error(msg)
                        else:
                            success, message = PortfolioService.deposit_funds(
                                st.session_state.portfolio_id, deposit_amount
                            )
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)

            with col2:
                st.markdown("**Wypłata środków**")

                with st.form("withdraw_form"):
                    withdraw_amount = st.number_input(
                        "Kwota wypłaty",
                        min_value=0.01,
                        max_value=max(current_balance, 0.01),
                        value=min(1000.0, current_balance) if current_balance > 0 else 0.01,
                        step=100.0,
                        key="withdraw_amount"
                    )

                    if st.form_submit_button("Wypłać"):
                        if withdraw_amount > current_balance:
                            st.error("Niewystarczające środki")
                        else:
                            success, message = PortfolioService.withdraw_funds(
                                st.session_state.portfolio_id, withdraw_amount
                            )
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)

    with tab4:
        st.subheader("Ustawienia systemu")

        # Database status
        st.markdown("**Status bazy danych**")

        success, message = test_connection()
        if success:
            st.success(f"Połączenie: {message}")
        else:
            st.error(f"Błąd połączenia: {message}")

        # Data status
        status = DataLoader.check_data_status()

        col1, col2 = st.columns(2)

        with col1:
            st.write(f"Giełdy: {status.get('exchanges_count', 0)}")
            st.write(f"Sektory: {status.get('sectors_count', 0)}")
            st.write(f"Instrumenty: {status.get('instruments_count', 0)}")

        with col2:
            st.write(f"Rekordy cenowe: {status.get('price_records_count', 0)}")
            date_range = status.get('date_range')
            if date_range:
                st.write(f"Zakres dat: {date_range[0]} - {date_range[1]}")

        st.divider()

        # Data refresh option
        st.markdown("**Aktualizacja danych rynkowych**")

        if st.button("Odśwież dane cenowe"):
            with st.spinner("Aktualizacja danych..."):
                # Re-initialize to get latest data
                success, messages = DataLoader.initialize_all()

                if success:
                    st.success("Dane zaktualizowane!")
                    for msg in messages:
                        st.info(msg)
                else:
                    st.error("Błąd podczas aktualizacji")
                    for msg in messages:
                        st.error(msg)

        st.divider()

        # About section
        st.markdown("**O aplikacji**")
        st.write("Symulator Giełdy - edukacyjna aplikacja do nauki inwestowania.")
        st.write("Wersja: 1.0.0")
        st.write("Prowizja od transakcji: 0.39%")

        st.caption("Dane rynkowe pochodzą z Yahoo Finance i służą wyłącznie celom edukacyjnym.")


if __name__ == "__main__":
    main()
