"""
Market page - Market quotations and instrument browser.
"""

import streamlit as st
import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.market_service import MarketService
from components.tables import Tables
from components.charts import Charts
from config import APP_CONFIG


def check_login():
    """Check if user is logged in."""
    if not st.session_state.get('logged_in', False):
        st.warning("Musisz się zalogować, aby zobaczyć tę stronę.")
        st.stop()


def main():
    st.set_page_config(
        page_title="Rynek - Symulator Giełdy",
        page_icon=APP_CONFIG['page_icon'],
        layout=APP_CONFIG['layout']
    )

    check_login()

    st.title("Rynek")

    simulation_date = st.session_state.get('simulation_date', date.today())
    is_time_travel = st.session_state.get('is_time_travel', False)

    if is_time_travel:
        st.info(f"Wyświetlanie notowań z dnia: {simulation_date}")

    # Filters
    col1, col2 = st.columns([2, 1])

    with col1:
        # Get sectors for filter
        sectors = MarketService.get_all_sectors()
        sector_options = {"Wszystkie sektory": None}
        for sector in sectors:
            sector_options[sector.get('nazwa_sektora', 'N/A')] = sector.get('sector_id')

        selected_sector_name = st.selectbox(
            "Filtruj po sektorze",
            options=list(sector_options.keys())
        )
        selected_sector_id = sector_options[selected_sector_name]

    with col2:
        view_mode = st.radio(
            "Widok",
            ["Lista", "Tabela"],
            horizontal=True
        )

    # Get instruments with prices
    instruments = MarketService.get_instruments_with_prices(simulation_date if is_time_travel else None)

    # Filter by sector if selected
    if selected_sector_id:
        instruments = [i for i in instruments if i.get('sector_id') == selected_sector_id]

    if not instruments:
        st.warning("Brak instrumentów spełniających kryteria.")
        return

    # Sort options
    sort_options = {
        "Symbol (A-Z)": lambda x: x.get('symbol', ''),
        "Symbol (Z-A)": lambda x: x.get('symbol', ''),
        "Cena (rosnąco)": lambda x: float(x.get('cena_zamkniecia', 0) or 0),
        "Cena (malejąco)": lambda x: float(x.get('cena_zamkniecia', 0) or 0),
        "Zmiana % (rosnąco)": lambda x: float(x.get('zmiana_procent', 0) or 0),
        "Zmiana % (malejąco)": lambda x: float(x.get('zmiana_procent', 0) or 0),
    }

    sort_by = st.selectbox("Sortuj", options=list(sort_options.keys()))
    reverse = "malejąco" in sort_by or "Z-A" in sort_by
    instruments = sorted(instruments, key=sort_options[sort_by], reverse=reverse)

    st.divider()

    # Display instruments
    if view_mode == "Lista":
        def on_buy(instrument):
            st.session_state['buy_instrument_id'] = instrument.get('instrument_id')
            st.switch_page("pages/2_Kupno.py")

        Tables.instruments_table(
            instruments,
            currency='USD',
            on_buy_click=on_buy
        )
    else:
        df = Tables.instruments_dataframe(instruments)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Cena": st.column_config.NumberColumn(format="%.2f"),
                "Zmiana": st.column_config.NumberColumn(format="%.2f"),
                "Zmiana %": st.column_config.NumberColumn(format="%.2f%%"),
                "Wolumen": st.column_config.NumberColumn(format="%d"),
            }
        )

    # Chart section
    st.divider()
    st.subheader("Wykres instrumentu")

    # Instrument selector for chart
    instrument_for_chart = st.selectbox(
        "Wybierz instrument",
        options=[i.get('symbol') for i in instruments],
        key="chart_instrument"
    )

    if instrument_for_chart:
        selected_inst = next((i for i in instruments if i.get('symbol') == instrument_for_chart), None)

        if selected_inst:
            instrument_id = selected_inst.get('instrument_id')

            # Date range for chart
            col1, col2, col3 = st.columns([1, 1, 2])

            min_date, max_date = MarketService.get_date_range()

            with col1:
                chart_start = st.date_input(
                    "Od",
                    value=max_date - timedelta(days=30) if max_date else date.today() - timedelta(days=30),
                    min_value=min_date,
                    max_value=max_date
                )

            with col2:
                chart_end = st.date_input(
                    "Do",
                    value=max_date if max_date else date.today(),
                    min_value=min_date,
                    max_value=max_date
                )

            with col3:
                chart_type = st.radio(
                    "Typ wykresu",
                    ["Świecowy", "Liniowy"],
                    horizontal=True
                )

            # Get price history
            price_history = MarketService.get_price_history(instrument_id, chart_start, chart_end)

            if price_history:
                if chart_type == "Świecowy":
                    fig = Charts.candlestick_chart(price_history, instrument_for_chart)
                else:
                    fig = Charts.line_chart(price_history, instrument_for_chart)

                st.plotly_chart(fig, use_container_width=True)

                # Quick buy button
                if st.button(f"Kup {instrument_for_chart}", use_container_width=True):
                    st.session_state['buy_instrument_id'] = instrument_id
                    st.switch_page("pages/2_Kupno.py")
            else:
                st.warning("Brak danych historycznych dla wybranego okresu.")

    # Market statistics
    st.divider()
    st.subheader("Statystyki rynku")

    col1, col2, col3 = st.columns(3)

    # Calculate statistics
    prices = [float(i.get('cena_zamkniecia', 0) or 0) for i in instruments if i.get('cena_zamkniecia')]
    changes = [float(i.get('zmiana_procent', 0) or 0) for i in instruments if i.get('zmiana_procent') is not None]

    with col1:
        st.metric("Liczba instrumentów", len(instruments))

    with col2:
        if changes:
            gainers = len([c for c in changes if c > 0])
            losers = len([c for c in changes if c < 0])
            st.metric("Wzrosty / Spadki", f"{gainers} / {losers}")

    with col3:
        if changes:
            avg_change = sum(changes) / len(changes)
            sign = "+" if avg_change > 0 else ""
            st.metric("Średnia zmiana", f"{sign}{avg_change:.2f}%")

    # Sector breakdown chart
    if instruments:
        fig = Charts.sector_distribution_bar(instruments, "Rozkład instrumentów wg sektorów")
        st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
