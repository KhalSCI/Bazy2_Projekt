"""
Portfolio page - Portfolio dashboard with time travel feature.
"""

import streamlit as st
import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.portfolio_service import PortfolioService
from services.market_service import MarketService
from components.tables import Tables
from components.charts import Charts
from config import APP_CONFIG


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
        page_title="Portfel - Symulator Giełdy",
        page_icon=APP_CONFIG['page_icon'],
        layout=APP_CONFIG['layout']
    )

    check_login()

    st.title("Portfel")

    portfolio_id = st.session_state.portfolio_id
    simulation_date = st.session_state.get('simulation_date', date.today())
    is_time_travel = st.session_state.get('is_time_travel', False)

    if is_time_travel:
        st.info(f"Wyświetlanie danych historycznych z dnia: {simulation_date}")

    # Portfolio summary
    summary = PortfolioService.get_portfolio_summary(portfolio_id)

    if not summary:
        st.error("Nie można pobrać danych portfela.")
        return

    currency = summary.get('waluta_portfela', 'USD')
    saldo = float(summary.get('saldo_gotowkowe', 0) or 0)

    # Get positions (with time travel if enabled) - needed for metrics calculation
    if is_time_travel:
        positions = PortfolioService.get_positions_for_date(portfolio_id, simulation_date)
    else:
        positions = PortfolioService.get_positions(portfolio_id)

    # Calculate values based on time travel
    if is_time_travel:
        # Calculate from positions for historical date
        wartosc_pozycji = sum(float(p.get('wartosc_biezaca', 0) or 0) for p in positions)
        zysk_strata = sum(float(p.get('zysk_strata', 0) or 0) for p in positions)
        wartosc_calkowita = saldo + wartosc_pozycji
    else:
        wartosc_calkowita = float(summary.get('wartosc_calkowita', 0) or 0)
        wartosc_pozycji = float(summary.get('wartosc_pozycji', 0) or 0)
        zysk_strata = float(summary.get('zysk_strata_pozycji', 0) or 0)

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

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
        if wartosc_pozycji > 0:
            sign = "+" if zysk_strata > 0 else ""
            zysk_procent = (zysk_strata / (wartosc_pozycji - zysk_strata)) * 100 if wartosc_pozycji != zysk_strata else 0
            st.metric(
                label="Zysk/Strata",
                value=f"{sign}{zysk_strata:,.2f} {currency}",
                delta=f"{sign}{zysk_procent:.2f}%"
            )
        else:
            st.metric(label="Zysk/Strata", value="-")

    st.divider()

    # Tabs for different views
    tab1, tab2 = st.tabs(["Pozycje", "Wykres"])

    with tab1:
        st.subheader("Twoje pozycje")

        # positions already fetched above for metrics calculation
        if positions:
            # Option to show as table or cards
            view_mode = st.radio(
                "Widok",
                ["Karty", "Tabela"],
                horizontal=True,
                label_visibility="collapsed"
            )

            if view_mode == "Karty":
                def on_sell(position):
                    st.session_state['sell_instrument_id'] = position.get('instrument_id')
                    st.session_state['sell_symbol'] = position.get('symbol')
                    st.switch_page("pages/3_Sprzedaz.py")

                Tables.positions_table(positions, currency, on_sell_click=on_sell)
            else:
                df = Tables.positions_dataframe(positions, currency)
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Ilość": st.column_config.NumberColumn(format="%.4f"),
                        "Śr. cena zakupu": st.column_config.NumberColumn(format="%.2f"),
                        "Wartość zakupu": st.column_config.NumberColumn(format="%.2f"),
                        "Wartość bieżąca": st.column_config.NumberColumn(format="%.2f"),
                        "Zysk/Strata": st.column_config.NumberColumn(format="%.2f"),
                        "Zysk %": st.column_config.NumberColumn(format="%.2f%%"),
                    }
                )
        else:
            st.info("Nie masz jeszcze żadnych pozycji. Przejdź do sekcji 'Kupno', aby rozpocząć inwestowanie.")

            if st.button("Przejdź do kupna"):
                st.switch_page("pages/2_Kupno.py")

    with tab2:
        st.subheader("Struktura portfela")

        if positions:
            col1, col2 = st.columns(2)

            with col1:
                # Pie chart of portfolio composition
                fig = Charts.portfolio_composition_pie(positions)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Summary statistics
                st.markdown("**Podsumowanie pozycji**")

                total_invested = sum(float(p.get('wartosc_zakupu', 0) or 0) for p in positions)
                total_current = sum(float(p.get('wartosc_biezaca', 0) or 0) for p in positions)
                total_gain = sum(float(p.get('zysk_strata', 0) or 0) for p in positions)

                st.write(f"Liczba pozycji: **{len(positions)}**")
                st.write(f"Zainwestowano: **{total_invested:,.2f} {currency}**")
                st.write(f"Wartość bieżąca: **{total_current:,.2f} {currency}**")

                if total_invested > 0:
                    overall_gain_pct = (total_gain / total_invested) * 100
                    sign = "+" if total_gain > 0 else ""
                    color = "green" if total_gain >= 0 else "red"
                    st.markdown(
                        f"Całkowity zysk: <span style='color:{color}'>**{sign}{total_gain:,.2f} {currency} ({sign}{overall_gain_pct:.2f}%)**</span>",
                        unsafe_allow_html=True
                    )

                # Best and worst performers
                if len(positions) > 1:
                    sorted_by_gain = sorted(positions, key=lambda x: float(x.get('zysk_strata_procent', 0) or 0), reverse=True)

                    st.markdown("---")
                    best = sorted_by_gain[0]
                    best_pct = float(best.get('zysk_strata_procent', 0) or 0)
                    st.write(f"Najlepsza pozycja: **{best.get('symbol')}** ({'+' if best_pct > 0 else ''}{best_pct:.2f}%)")

                    worst = sorted_by_gain[-1]
                    worst_pct = float(worst.get('zysk_strata_procent', 0) or 0)
                    st.write(f"Najgorsza pozycja: **{worst.get('symbol')}** ({'+' if worst_pct > 0 else ''}{worst_pct:.2f}%)")

        else:
            st.info("Brak danych do wyświetlenia wykresu.")

    # Quick actions
    st.divider()
    st.subheader("Szybkie akcje")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Kup akcje", use_container_width=True):
            st.switch_page("pages/2_Kupno.py")

    with col2:
        if st.button("Sprzedaj akcje", use_container_width=True):
            st.switch_page("pages/3_Sprzedaz.py")

    with col3:
        if st.button("Zobacz rynek", use_container_width=True):
            st.switch_page("pages/4_Rynek.py")


if __name__ == "__main__":
    main()
