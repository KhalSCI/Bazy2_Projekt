"""
Buy order page - Form for placing buy orders.
"""

import streamlit as st
import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.portfolio_service import PortfolioService
from services.market_service import MarketService
from services.order_service import OrderService
from utils.validators import validate_quantity, validate_sufficient_funds
from config import APP_CONFIG, ORDER_TYPES


def check_login():
    """Check if user is logged in."""
    if not st.session_state.get('logged_in', False):
        st.warning("Musisz się zalogować, aby zobaczyć tę stronę.")
        st.stop()

    if not st.session_state.get('portfolio_id'):
        st.warning("Nie masz żadnego portfela. Przejdź do ustawień, aby utworzyć portfel.")
        st.stop()


def main():
    st.set_page_config(
        page_title="Kupno - Symulator Giełdy",
        page_icon=APP_CONFIG['page_icon'],
        layout=APP_CONFIG['layout']
    )

    check_login()

    st.title("Kupno akcji")

    portfolio_id = st.session_state.portfolio_id
    simulation_date = st.session_state.get('simulation_date', date.today())
    is_time_travel = st.session_state.get('is_time_travel', False)

    # Get portfolio info
    portfolio = PortfolioService.get_portfolio(portfolio_id)
    if not portfolio:
        st.error("Nie można pobrać danych portfela.")
        return

    currency = portfolio.get('waluta_portfela', 'USD')
    available_cash = float(portfolio.get('saldo_gotowkowe', 0) or 0)

    # Show available cash
    st.info(f"Dostępne środki: **{available_cash:,.2f} {currency}**")

    if is_time_travel:
        st.warning(f"Tryb historyczny - ceny z dnia: {simulation_date}")

    # Get instruments
    instruments = MarketService.get_instruments_with_prices(simulation_date if is_time_travel else None)

    if not instruments:
        st.error("Brak dostępnych instrumentów.")
        return

    # Create instrument options
    instrument_options = {}
    for inst in instruments:
        symbol = inst.get('symbol', 'N/A')
        nazwa = inst.get('nazwa_pelna', '')
        cena = inst.get('cena_zamkniecia')
        if cena:
            label = f"{symbol} - {nazwa[:30]}... ({float(cena):,.2f} {currency})"
        else:
            label = f"{symbol} - {nazwa[:30]}... (brak ceny)"
        instrument_options[label] = inst

    # Check if instrument was pre-selected (from market page)
    preselected_id = st.session_state.get('buy_instrument_id')
    preselected_index = 0
    if preselected_id:
        for i, (label, inst) in enumerate(instrument_options.items()):
            if inst.get('instrument_id') == preselected_id:
                preselected_index = i
                break
        # Clear the preselection
        del st.session_state['buy_instrument_id']

    # Order form
    st.subheader("Nowe zlecenie kupna")

    with st.form("buy_order_form"):
        # Instrument selection
        selected_label = st.selectbox(
            "Wybierz instrument",
            options=list(instrument_options.keys()),
            index=preselected_index
        )

        selected_instrument = instrument_options[selected_label]
        instrument_id = selected_instrument.get('instrument_id')
        current_price = selected_instrument.get('cena_zamkniecia')

        col1, col2 = st.columns(2)

        with col1:
            # Order type
            order_type = st.selectbox(
                "Typ zlecenia",
                options=list(ORDER_TYPES.keys()),
                format_func=lambda x: ORDER_TYPES[x]
            )

        with col2:
            # Quantity
            quantity = st.number_input(
                "Ilość akcji",
                min_value=0.0001,
                value=1.0,
                step=1.0,
                format="%.4f"
            )

        # Limit price for LIMIT orders
        limit_price = None
        if order_type == 'LIMIT':
            default_limit = float(current_price) if current_price else 100.0
            limit_price = st.number_input(
                "Cena limitu",
                min_value=0.01,
                value=default_limit,
                step=0.01,
                format="%.2f",
                help="Zlecenie zostanie wykonane gdy cena spadnie do lub poniżej tej wartości"
            )

        # Calculate costs
        if current_price:
            execution_price = limit_price if order_type == 'LIMIT' else float(current_price)
            cost_details = OrderService.calculate_order_cost(quantity, execution_price)

            st.divider()
            st.markdown("**Podsumowanie zlecenia:**")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Wartość", f"{cost_details['wartosc']:,.2f} {currency}")
            with col2:
                st.metric("Prowizja (0.39%)", f"{cost_details['prowizja']:,.2f} {currency}")
            with col3:
                st.metric("Koszt całkowity", f"{cost_details['koszt_calkowity']:,.2f} {currency}")

            # Check if enough funds
            if cost_details['koszt_calkowity'] > available_cash:
                st.error(f"Niewystarczające środki! Potrzebujesz: {cost_details['koszt_calkowity']:,.2f} {currency}")

        submit = st.form_submit_button("Złóż zlecenie kupna", use_container_width=True)

        if submit:
            # Validation
            if not current_price:
                st.error("Brak dostępnej ceny dla tego instrumentu.")
            else:
                valid_qty, qty_msg = validate_quantity(quantity)
                if not valid_qty:
                    st.error(qty_msg)
                else:
                    execution_price = limit_price if order_type == 'LIMIT' else float(current_price)
                    cost_details = OrderService.calculate_order_cost(quantity, execution_price)

                    valid_funds, funds_msg = validate_sufficient_funds(
                        cost_details['koszt_calkowity'],
                        available_cash,
                        currency
                    )

                    if not valid_funds:
                        st.error(funds_msg)
                    else:
                        # Execute order
                        if order_type == 'MARKET':
                            success, message = OrderService.create_and_execute_buy(
                                portfolio_id, instrument_id, quantity, execution_price
                            )
                        else:
                            success, message, order_id = OrderService.create_limit_buy(
                                portfolio_id, instrument_id, quantity, limit_price
                            )

                        if success:
                            st.success(f"Zlecenie złożone pomyślnie! {message}")
                            st.balloons()

                            # Refresh portfolio data
                            PortfolioService.update_positions(portfolio_id)
                        else:
                            st.error(f"Błąd: {message}")

    # Show instrument details
    if selected_instrument:
        st.divider()
        st.subheader(f"Szczegóły: {selected_instrument.get('symbol')}")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.write(f"**Nazwa:** {selected_instrument.get('nazwa_pelna', 'N/A')}")
            st.write(f"**Sektor:** {selected_instrument.get('nazwa_sektora', 'N/A')}")

        with col2:
            if current_price:
                st.write(f"**Cena:** {float(current_price):,.2f} {currency}")
            zmiana = selected_instrument.get('zmiana_procent')
            if zmiana is not None:
                sign = "+" if float(zmiana) > 0 else ""
                color = "green" if float(zmiana) >= 0 else "red"
                st.markdown(f"**Zmiana:** <span style='color:{color}'>{sign}{float(zmiana):.2f}%</span>", unsafe_allow_html=True)

        with col3:
            wolumen = selected_instrument.get('wolumen')
            if wolumen:
                st.write(f"**Wolumen:** {int(wolumen):,}")
            st.write(f"**Giełda:** {selected_instrument.get('kod_gieldy', 'N/A')}")


if __name__ == "__main__":
    main()
