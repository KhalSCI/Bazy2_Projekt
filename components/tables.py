"""
Table components for displaying data.
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Optional, Callable
from datetime import datetime


class Tables:
    """Data table components."""

    @staticmethod
    def positions_table(positions: List[Dict], currency: str = 'USD',
                       on_sell_click: Callable = None) -> None:
        """
        Display positions table with optional sell button.

        Args:
            positions: List of position dicts
            currency: Currency symbol
            on_sell_click: Callback when sell button is clicked
        """
        if not positions:
            st.info("Brak pozycji w portfelu")
            return

        for pos in positions:
            symbol = pos.get('symbol', 'N/A')
            nazwa = pos.get('nazwa_pelna', '')
            ilosc = float(pos.get('ilosc_akcji', 0) or 0)
            srednia_cena = float(pos.get('srednia_cena_zakupu', 0) or 0)
            wartosc_biezaca = float(pos.get('wartosc_biezaca', 0) or 0)
            zysk_strata = float(pos.get('zysk_strata', 0) or 0)
            zysk_procent = float(pos.get('zysk_strata_procent', 0) or 0)

            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])

                with col1:
                    st.markdown(f"**{symbol}**")
                    st.caption(nazwa[:30] + '...' if len(nazwa) > 30 else nazwa)

                with col2:
                    st.metric(
                        label="Ilość",
                        value=f"{ilosc:.4f}" if ilosc != int(ilosc) else f"{int(ilosc)}"
                    )

                with col3:
                    st.metric(
                        label="Wartość",
                        value=f"{wartosc_biezaca:,.2f} {currency}"
                    )

                with col4:
                    sign = "+" if zysk_strata > 0 else ""
                    st.metric(
                        label="Zysk/Strata",
                        value=f"{sign}{zysk_strata:,.2f} {currency}",
                        delta=f"{sign}{zysk_procent:.2f}%",
                        delta_color="normal"
                    )

                with col5:
                    if on_sell_click:
                        if st.button("Sprzedaj", key=f"sell_{pos.get('instrument_id')}"):
                            on_sell_click(pos)

                st.divider()

    @staticmethod
    def positions_dataframe(positions: List[Dict], currency: str = 'USD') -> pd.DataFrame:
        """
        Convert positions to formatted DataFrame.

        Args:
            positions: List of position dicts
            currency: Currency symbol

        Returns:
            Formatted DataFrame
        """
        if not positions:
            return pd.DataFrame()

        data = []
        for pos in positions:
            data.append({
                'Symbol': pos.get('symbol', 'N/A'),
                'Nazwa': pos.get('nazwa_pelna', ''),
                'Ilość': float(pos.get('ilosc_akcji', 0) or 0),
                'Śr. cena zakupu': float(pos.get('srednia_cena_zakupu', 0) or 0),
                'Wartość zakupu': float(pos.get('wartosc_zakupu', 0) or 0),
                'Wartość bieżąca': float(pos.get('wartosc_biezaca', 0) or 0),
                'Zysk/Strata': float(pos.get('zysk_strata', 0) or 0),
                'Zysk %': float(pos.get('zysk_strata_procent', 0) or 0),
            })

        df = pd.DataFrame(data)
        return df

    @staticmethod
    def orders_table(orders: List[Dict], on_cancel_click: Callable = None) -> None:
        """
        Display orders table with optional cancel button.

        Args:
            orders: List of order dicts
            on_cancel_click: Callback when cancel button is clicked
        """
        if not orders:
            st.info("Brak zleceń")
            return

        for order in orders:
            order_id = order.get('order_id')
            symbol = order.get('symbol', 'N/A')
            typ = order.get('typ_zlecenia', 'N/A')
            strona = order.get('strona_zlecenia', 'N/A')
            ilosc = float(order.get('ilosc', 0) or 0)
            limit_ceny = order.get('limit_ceny')
            status = order.get('status', 'N/A')
            data_utworzenia = order.get('data_utworzenia')

            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])

                with col1:
                    strona_color = "🟢" if strona == 'KUPNO' else "🔴"
                    st.markdown(f"{strona_color} **{symbol}**")
                    st.caption(f"{typ} - {strona}")

                with col2:
                    st.metric(label="Ilość", value=f"{ilosc:.4f}")

                with col3:
                    if limit_ceny:
                        st.metric(label="Limit ceny", value=f"{float(limit_ceny):,.2f}")
                    else:
                        st.metric(label="Limit ceny", value="Rynkowa")

                with col4:
                    status_emoji = {
                        'OCZEKUJACE': '⏳',
                        'WYKONANE': '✅',
                        'ANULOWANE': '❌',
                        'CZESCIOWE': '🔄'
                    }
                    st.markdown(f"{status_emoji.get(status, '')} {status}")
                    if data_utworzenia:
                        if isinstance(data_utworzenia, datetime):
                            st.caption(data_utworzenia.strftime('%Y-%m-%d %H:%M'))
                        else:
                            st.caption(str(data_utworzenia))

                with col5:
                    if on_cancel_click and status == 'OCZEKUJACE':
                        if st.button("Anuluj", key=f"cancel_{order_id}"):
                            on_cancel_click(order)

                st.divider()

    @staticmethod
    def transactions_table(transactions: List[Dict]) -> None:
        """
        Display transactions table.

        Args:
            transactions: List of transaction dicts
        """
        if not transactions:
            st.info("Brak transakcji")
            return

        data = []
        for tx in transactions:
            data.append({
                'Data': tx.get('data_transakcji'),
                'Symbol': tx.get('symbol', 'N/A'),
                'Typ': tx.get('typ_transakcji', 'N/A'),
                'Ilość': float(tx.get('ilosc', 0) or 0),
                'Cena': float(tx.get('cena_jednostkowa', 0) or 0),
                'Wartość': float(tx.get('wartosc_transakcji', 0) or 0),
                'Prowizja': float(tx.get('prowizja', 0) or 0),
                'Waluta': tx.get('waluta_transakcji', 'USD')
            })

        df = pd.DataFrame(data)

        # Format columns
        if not df.empty:
            df['Ilość'] = df['Ilość'].apply(lambda x: f"{x:.4f}")
            df['Cena'] = df['Cena'].apply(lambda x: f"{x:,.2f}")
            df['Wartość'] = df['Wartość'].apply(lambda x: f"{x:,.2f}")
            df['Prowizja'] = df['Prowizja'].apply(lambda x: f"{x:.2f}")

        st.dataframe(df, use_container_width=True, hide_index=True)

    @staticmethod
    def instruments_table(instruments: List[Dict], currency: str = 'USD',
                         on_buy_click: Callable = None) -> None:
        """
        Display instruments table with prices.

        Args:
            instruments: List of instrument dicts
            currency: Currency symbol
            on_buy_click: Callback when buy button is clicked
        """
        if not instruments:
            st.info("Brak instrumentów")
            return

        for inst in instruments:
            instrument_id = inst.get('instrument_id')
            symbol = inst.get('symbol', 'N/A')
            nazwa = inst.get('nazwa_pelna', '')
            sektor = inst.get('nazwa_sektora', 'N/A')
            cena = inst.get('cena_zamkniecia')
            zmiana = inst.get('zmiana')
            zmiana_procent = inst.get('zmiana_procent')

            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 1, 2, 2, 1])

                with col1:
                    st.markdown(f"**{symbol}**")
                    st.caption(nazwa[:35] + '...' if len(nazwa) > 35 else nazwa)

                with col2:
                    st.caption(sektor)

                with col3:
                    if cena:
                        st.metric(label="Cena", value=f"{float(cena):,.2f} {currency}")
                    else:
                        st.metric(label="Cena", value="Brak danych")

                with col4:
                    if zmiana is not None and zmiana_procent is not None:
                        color = "normal" if float(zmiana) >= 0 else "inverse"
                        sign = "+" if float(zmiana) > 0 else ""
                        st.metric(
                            label="Zmiana",
                            value=f"{sign}{float(zmiana):,.2f}",
                            delta=f"{sign}{float(zmiana_procent):.2f}%",
                            delta_color=color
                        )
                    else:
                        st.metric(label="Zmiana", value="-")

                with col5:
                    if on_buy_click and cena:
                        if st.button("Kup", key=f"buy_{instrument_id}"):
                            on_buy_click(inst)

                st.divider()

    @staticmethod
    def instruments_dataframe(instruments: List[Dict]) -> pd.DataFrame:
        """
        Convert instruments to formatted DataFrame.

        Args:
            instruments: List of instrument dicts

        Returns:
            Formatted DataFrame
        """
        if not instruments:
            return pd.DataFrame()

        data = []
        for inst in instruments:
            cena = inst.get('cena_zamkniecia')
            zmiana = inst.get('zmiana')
            zmiana_procent = inst.get('zmiana_procent')

            data.append({
                'Symbol': inst.get('symbol', 'N/A'),
                'Nazwa': inst.get('nazwa_pelna', ''),
                'Sektor': inst.get('nazwa_sektora', 'N/A'),
                'Cena': float(cena) if cena else None,
                'Zmiana': float(zmiana) if zmiana else None,
                'Zmiana %': float(zmiana_procent) if zmiana_procent else None,
                'Wolumen': inst.get('wolumen'),
                'Data': inst.get('data_notowan')
            })

        return pd.DataFrame(data)

    @staticmethod
    def styled_metric_row(metrics: List[Dict]) -> None:
        """
        Display a row of styled metrics.

        Args:
            metrics: List of dicts with 'label', 'value', and optional 'delta'
        """
        cols = st.columns(len(metrics))
        for col, metric in zip(cols, metrics):
            with col:
                if 'delta' in metric:
                    st.metric(
                        label=metric['label'],
                        value=metric['value'],
                        delta=metric.get('delta'),
                        delta_color=metric.get('delta_color', 'normal')
                    )
                else:
                    st.metric(label=metric['label'], value=metric['value'])
