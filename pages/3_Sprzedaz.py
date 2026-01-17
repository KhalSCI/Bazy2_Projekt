"""
Sell order page - Form for placing sell orders.
"""

import streamlit as st
import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.portfolio_service import PortfolioService
from services.market_service import MarketService
from services.order_service import OrderService
from utils.validators import validate_quantity, validate_sufficient_shares
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
        page_title="Sprzedaż - Symulator Giełdy",
        page_icon=APP_CONFIG['page_icon'],
        layout=APP_CONFIG['layout']
    )

    check_login()

    st.title("Sprzedaż akcji")

    portfolio_id = st.session_state.portfolio_id
    simulation_date = st.session_state.get('simulation_date', date.today())
    is_time_travel = st.session_state.get('is_time_travel', False)

    # Get portfolio info
    portfolio = PortfolioService.get_portfolio(portfolio_id)
    if not portfolio:
        st.error("Nie można pobrać danych portfela.")
        return

    currency = portfolio.get('waluta_portfela', 'USD')

    if is_time_travel:
        st.warning(f"Tryb historyczny - ceny z dnia: {simulation_date}")

    # Get positions (only owned instruments)
    if is_time_travel:
        positions = PortfolioService.get_positions_for_date(portfolio_id, simulation_date)
    else:
        positions = PortfolioService.get_positions(portfolio_id)

    if not positions:
        st.info("Nie posiadasz żadnych akcji do sprzedaży.")
        if st.button("Przejdź do kupna"):
            st.switch_page("pages/2_Kupno.py")
        return

    # Create position options
    position_options = {}
    for pos in positions:
        symbol = pos.get('symbol', 'N/A')
        ilosc = float(pos.get('ilosc_akcji', 0) or 0)
        label = f"{symbol} - {ilosc:.4f} szt."
        position_options[label] = pos

    # Check if instrument was pre-selected (from portfolio page)
    preselected_id = st.session_state.get('sell_instrument_id')
    preselected_index = 0
    if preselected_id:
        for i, (label, pos) in enumerate(position_options.items()):
            if pos.get('instrument_id') == preselected_id:
                preselected_index = i
                break
        # Clear the preselection
        if 'sell_instrument_id' in st.session_state:
            del st.session_state['sell_instrument_id']
        if 'sell_symbol' in st.session_state:
            del st.session_state['sell_symbol']

    # Order form
    st.subheader("Nowe zlecenie sprzedaży")

    with st.form("sell_order_form"):
        # Position selection
        selected_label = st.selectbox(
            "Wybierz pozycję do sprzedaży",
            options=list(position_options.keys()),
            index=preselected_index
        )

        selected_position = position_options[selected_label]
        instrument_id = selected_position.get('instrument_id')
        symbol = selected_position.get('symbol')
        owned_shares = float(selected_position.get('ilosc_akcji', 0) or 0)
        avg_purchase_price = float(selected_position.get('srednia_cena_zakupu', 0) or 0)

        # Get current price
        if is_time_travel:
            current_price = MarketService.get_price_for_date(instrument_id, simulation_date)
        else:
            current_price = MarketService.get_current_price(instrument_id)

        # Position info
        st.info(f"Posiadasz: **{owned_shares:.4f}** akcji {symbol} | "
                f"Średnia cena zakupu: **{avg_purchase_price:,.2f} {currency}**")

        col1, col2 = st.columns(2)

        with col1:
            # Order type
            order_type = st.selectbox(
                "Typ zlecenia",
                options=list(ORDER_TYPES.keys()),
                format_func=lambda x: ORDER_TYPES[x]
            )

        with col2:
            # Quantity with max button
            quantity = st.number_input(
                "Ilość akcji",
                min_value=0.0001,
                max_value=owned_shares,
                value=min(1.0, owned_shares),
                step=1.0,
                format="%.4f"
            )

        # Sell all button
        if st.checkbox("Sprzedaj wszystkie"):
            quantity = owned_shares

        # Limit price for LIMIT orders
        limit_price = None
        if order_type == 'LIMIT':
            default_limit = float(current_price) if current_price else avg_purchase_price
            limit_price = st.number_input(
                "Cena limitu",
                min_value=0.01,
                value=default_limit,
                step=0.01,
                format="%.2f",
                help="Zlecenie zostanie wykonane gdy cena wzrośnie do lub powyżej tej wartości"
            )

        # Calculate proceeds and gain/loss
        if current_price:
            execution_price = limit_price if order_type == 'LIMIT' else float(current_price)
            proceeds_details = OrderService.calculate_order_proceeds(quantity, execution_price)

            # Calculate gain/loss
            purchase_value = quantity * avg_purchase_price
            sale_value = proceeds_details['przychod_netto']
            gain_loss = sale_value - purchase_value
            gain_loss_pct = ((execution_price - avg_purchase_price) / avg_purchase_price * 100) if avg_purchase_price > 0 else 0

            st.divider()
            st.markdown("**Podsumowanie zlecenia:**")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Wartość sprzedaży", f"{proceeds_details['wartosc']:,.2f} {currency}")
            with col2:
                st.metric("Prowizja (0.39%)", f"{proceeds_details['prowizja']:,.2f} {currency}")
            with col3:
                st.metric("Przychód netto", f"{proceeds_details['przychod_netto']:,.2f} {currency}")

            # Gain/loss preview
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Wartość zakupu", f"{purchase_value:,.2f} {currency}")
            with col2:
                sign = "+" if gain_loss > 0 else ""
                color = "normal" if gain_loss >= 0 else "inverse"
                st.metric(
                    "Zysk/Strata",
                    f"{sign}{gain_loss:,.2f} {currency}",
                    delta=f"{sign}{gain_loss_pct:.2f}%",
                    delta_color=color
                )

        submit = st.form_submit_button("Złóż zlecenie sprzedaży", use_container_width=True)

        if submit:
            # Validation
            if not current_price:
                st.error("Brak dostępnej ceny dla tego instrumentu.")
            else:
                valid_qty, qty_msg = validate_quantity(quantity, owned_shares)
                if not valid_qty:
                    st.error(qty_msg)
                else:
                    valid_shares, shares_msg = validate_sufficient_shares(quantity, owned_shares, symbol)
                    if not valid_shares:
                        st.error(shares_msg)
                    else:
                        execution_price = limit_price if order_type == 'LIMIT' else float(current_price)

                        # Execute order
                        if order_type == 'MARKET':
                            success, message = OrderService.create_and_execute_sell(
                                portfolio_id, instrument_id, quantity, execution_price
                            )
                        else:
                            success, message, order_id = OrderService.create_limit_sell(
                                portfolio_id, instrument_id, quantity, limit_price
                            )

                        if success:
                            st.success(f"Zlecenie złożone pomyślnie! {message}")
                            st.balloons()

                            # Refresh portfolio data
                            PortfolioService.update_positions(portfolio_id)
                        else:
                            st.error(f"Błąd: {message}")

    # Position details
    if selected_position:
        st.divider()
        st.subheader(f"Szczegóły pozycji: {symbol}")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.write(f"**Nazwa:** {selected_position.get('nazwa_pelna', 'N/A')}")
            st.write(f"**Ilość:** {owned_shares:.4f}")

        with col2:
            st.write(f"**Śr. cena zakupu:** {avg_purchase_price:,.2f} {currency}")
            if current_price:
                st.write(f"**Cena bieżąca:** {float(current_price):,.2f} {currency}")

        with col3:
            wartosc_zakupu = float(selected_position.get('wartosc_zakupu', 0) or 0)
            wartosc_biezaca = float(selected_position.get('wartosc_biezaca', 0) or 0)
            zysk_strata = float(selected_position.get('zysk_strata', 0) or 0)
            zysk_procent = float(selected_position.get('zysk_strata_procent', 0) or 0)

            st.write(f"**Wartość zakupu:** {wartosc_zakupu:,.2f} {currency}")
            sign = "+" if zysk_strata > 0 else ""
            color = "green" if zysk_strata >= 0 else "red"
            st.markdown(
                f"**Zysk/Strata:** <span style='color:{color}'>{sign}{zysk_strata:,.2f} {currency} ({sign}{zysk_procent:.2f}%)</span>",
                unsafe_allow_html=True
            )


if __name__ == "__main__":
    main()
