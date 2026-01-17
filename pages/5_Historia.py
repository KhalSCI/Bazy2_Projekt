"""
History page - Order and transaction history.
"""

import streamlit as st
import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.order_service import OrderService, TransactionService
from components.tables import Tables
from config import APP_CONFIG, ORDER_STATUSES


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
        page_title="Historia - Symulator Giełdy",
        page_icon=APP_CONFIG['page_icon'],
        layout=APP_CONFIG['layout']
    )

    check_login()

    st.title("Historia")

    portfolio_id = st.session_state.portfolio_id

    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "Oczekujące",
        "Wykonane",
        "Anulowane",
        "Transakcje"
    ])

    with tab1:
        st.subheader("Oczekujące zlecenia")

        pending_orders = OrderService.get_pending_orders(portfolio_id)

        if pending_orders:
            def on_cancel(order):
                order_id = order.get('order_id')
                success, message = OrderService.cancel_order(order_id)
                if success:
                    st.success(f"Zlecenie #{order_id} anulowane")
                    st.rerun()
                else:
                    st.error(f"Błąd: {message}")

            Tables.orders_table(pending_orders, on_cancel_click=on_cancel)

            # Bulk cancel option
            if len(pending_orders) > 1:
                if st.button("Anuluj wszystkie oczekujące zlecenia"):
                    cancelled = 0
                    for order in pending_orders:
                        success, _ = OrderService.cancel_order(order.get('order_id'))
                        if success:
                            cancelled += 1
                    st.success(f"Anulowano {cancelled} zleceń")
                    st.rerun()
        else:
            st.info("Brak oczekujących zleceń")

    with tab2:
        st.subheader("Wykonane zlecenia")

        executed_orders = OrderService.get_executed_orders(portfolio_id)

        if executed_orders:
            for order in executed_orders:
                symbol = order.get('symbol', 'N/A')
                strona = order.get('strona_zlecenia', 'N/A')
                ilosc = float(order.get('ilosc', 0) or 0)
                data_wykonania = order.get('data_wykonania')

                strona_emoji = "🟢" if strona == 'KUPNO' else "🔴"

                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

                    with col1:
                        st.markdown(f"{strona_emoji} **{symbol}**")
                        st.caption(strona)

                    with col2:
                        st.metric(label="Ilość", value=f"{ilosc:.4f}")

                    with col3:
                        limit_ceny = order.get('limit_ceny')
                        if limit_ceny:
                            st.metric(label="Cena", value=f"{float(limit_ceny):,.2f}")
                        else:
                            st.metric(label="Cena", value="Rynkowa")

                    with col4:
                        if data_wykonania:
                            st.write("Wykonano:")
                            st.caption(str(data_wykonania)[:19])

                    st.divider()
        else:
            st.info("Brak wykonanych zleceń")

    with tab3:
        st.subheader("Anulowane zlecenia")

        all_orders = OrderService.get_orders_by_portfolio(portfolio_id)
        cancelled_orders = [o for o in all_orders if o.get('status') == 'ANULOWANE']

        if cancelled_orders:
            for order in cancelled_orders:
                symbol = order.get('symbol', 'N/A')
                strona = order.get('strona_zlecenia', 'N/A')
                ilosc = float(order.get('ilosc', 0) or 0)
                data_utworzenia = order.get('data_utworzenia')

                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

                    with col1:
                        st.markdown(f"❌ **{symbol}**")
                        st.caption(strona)

                    with col2:
                        st.metric(label="Ilość", value=f"{ilosc:.4f}")

                    with col3:
                        limit_ceny = order.get('limit_ceny')
                        if limit_ceny:
                            st.metric(label="Limit", value=f"{float(limit_ceny):,.2f}")
                        else:
                            st.metric(label="Limit", value="-")

                    with col4:
                        if data_utworzenia:
                            st.write("Utworzono:")
                            st.caption(str(data_utworzenia)[:19])

                    st.divider()
        else:
            st.info("Brak anulowanych zleceń")

    with tab4:
        st.subheader("Historia transakcji")

        # Date filter
        col1, col2 = st.columns(2)

        with col1:
            start_date = st.date_input(
                "Od daty",
                value=date.today() - timedelta(days=30)
            )

        with col2:
            end_date = st.date_input(
                "Do daty",
                value=date.today()
            )

        # Get transactions
        if start_date and end_date:
            transactions = TransactionService.get_transactions_by_date_range(
                portfolio_id, start_date, end_date
            )
        else:
            transactions = TransactionService.get_transactions_by_portfolio(portfolio_id)

        if transactions:
            Tables.transactions_table(transactions)

            # Summary statistics
            st.divider()
            st.subheader("Podsumowanie")

            col1, col2, col3, col4 = st.columns(4)

            total_buy = sum(
                float(t.get('wartosc_transakcji', 0) or 0)
                for t in transactions
                if t.get('typ_transakcji') == 'KUPNO'
            )
            total_sell = sum(
                float(t.get('wartosc_transakcji', 0) or 0)
                for t in transactions
                if t.get('typ_transakcji') == 'SPRZEDAZ'
            )
            total_commission = sum(
                float(t.get('prowizja', 0) or 0)
                for t in transactions
            )

            with col1:
                st.metric("Liczba transakcji", len(transactions))

            with col2:
                st.metric("Wartość zakupów", f"{total_buy:,.2f}")

            with col3:
                st.metric("Wartość sprzedaży", f"{total_sell:,.2f}")

            with col4:
                st.metric("Suma prowizji", f"{total_commission:,.2f}")

        else:
            st.info("Brak transakcji w wybranym okresie")

    # Export option
    st.divider()
    st.subheader("Eksport danych")

    export_type = st.selectbox(
        "Wybierz dane do eksportu",
        ["Wszystkie zlecenia", "Wykonane zlecenia", "Transakcje"]
    )

    if st.button("Eksportuj do CSV"):
        import pandas as pd

        if export_type == "Wszystkie zlecenia":
            data = OrderService.get_orders_by_portfolio(portfolio_id)
        elif export_type == "Wykonane zlecenia":
            data = OrderService.get_executed_orders(portfolio_id)
        else:
            data = TransactionService.get_transactions_by_portfolio(portfolio_id)

        if data:
            df = pd.DataFrame(data)
            csv = df.to_csv(index=False)
            st.download_button(
                label="Pobierz CSV",
                data=csv,
                file_name=f"{export_type.lower().replace(' ', '_')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("Brak danych do eksportu")


if __name__ == "__main__":
    main()
