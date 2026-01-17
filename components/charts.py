"""
Chart components using Plotly.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import List, Dict, Optional
from datetime import date
import pandas as pd


class Charts:
    """Plotly chart components."""

    @staticmethod
    def portfolio_value_chart(history_data: List[Dict], currency: str = 'USD',
                             title: str = 'Wartość portfela w czasie') -> go.Figure:
        """
        Create a line chart showing portfolio value over time.

        Args:
            history_data: List of dicts with 'data' and 'wartosc' keys
            currency: Currency symbol
            title: Chart title

        Returns:
            Plotly figure
        """
        if not history_data:
            fig = go.Figure()
            fig.add_annotation(
                text="Brak danych do wyświetlenia",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig

        df = pd.DataFrame(history_data)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['data'],
            y=df['wartosc'],
            mode='lines+markers',
            name='Wartość portfela',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=6),
            hovertemplate='%{x}<br>Wartość: %{y:,.2f} ' + currency + '<extra></extra>'
        ))

        fig.update_layout(
            title=title,
            xaxis_title='Data',
            yaxis_title=f'Wartość ({currency})',
            hovermode='x unified',
            showlegend=False,
            height=400
        )

        return fig

    @staticmethod
    def candlestick_chart(price_data: List[Dict], symbol: str,
                         title: str = None) -> go.Figure:
        """
        Create a candlestick chart for stock prices.

        Args:
            price_data: List of OHLCV dicts
            symbol: Stock symbol
            title: Optional title

        Returns:
            Plotly figure
        """
        if not price_data:
            fig = go.Figure()
            fig.add_annotation(
                text="Brak danych do wyświetlenia",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig

        df = pd.DataFrame(price_data)

        # Rename columns if needed
        column_map = {
            'data_notowan': 'data',
            'cena_otwarcia': 'open',
            'cena_max': 'high',
            'cena_min': 'low',
            'cena_zamkniecia': 'close',
            'wolumen': 'volume'
        }
        df = df.rename(columns=column_map)

        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3]
        )

        # Candlestick
        fig.add_trace(go.Candlestick(
            x=df['data'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='OHLC',
            increasing_line_color='#26a69a',
            decreasing_line_color='#ef5350'
        ), row=1, col=1)

        # Volume bars
        colors = ['#26a69a' if close >= open else '#ef5350'
                  for close, open in zip(df['close'], df['open'])]

        fig.add_trace(go.Bar(
            x=df['data'],
            y=df['volume'],
            name='Wolumen',
            marker_color=colors,
            opacity=0.7
        ), row=2, col=1)

        fig.update_layout(
            title=title or f'{symbol} - Wykres świecowy',
            xaxis_rangeslider_visible=False,
            height=500,
            showlegend=False
        )

        fig.update_yaxes(title_text='Cena', row=1, col=1)
        fig.update_yaxes(title_text='Wolumen', row=2, col=1)

        return fig

    @staticmethod
    def line_chart(price_data: List[Dict], symbol: str,
                  title: str = None) -> go.Figure:
        """
        Create a simple line chart for stock prices.

        Args:
            price_data: List of dicts with 'data' and 'close' (or 'cena_zamkniecia')
            symbol: Stock symbol
            title: Optional title

        Returns:
            Plotly figure
        """
        if not price_data:
            fig = go.Figure()
            fig.add_annotation(
                text="Brak danych do wyświetlenia",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig

        df = pd.DataFrame(price_data)

        # Handle different column names
        date_col = 'data' if 'data' in df.columns else 'data_notowan'
        close_col = 'close' if 'close' in df.columns else 'cena_zamkniecia'

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df[date_col],
            y=df[close_col],
            mode='lines',
            name=symbol,
            line=dict(color='#1f77b4', width=2),
            fill='tozeroy',
            fillcolor='rgba(31, 119, 180, 0.1)',
            hovertemplate='%{x}<br>Cena: %{y:,.2f}<extra></extra>'
        ))

        fig.update_layout(
            title=title or f'{symbol} - Cena zamknięcia',
            xaxis_title='Data',
            yaxis_title='Cena',
            hovermode='x unified',
            height=400
        )

        return fig

    @staticmethod
    def portfolio_composition_pie(positions: List[Dict],
                                  title: str = 'Skład portfela') -> go.Figure:
        """
        Create a pie chart showing portfolio composition.

        Args:
            positions: List of position dicts with 'symbol' and 'wartosc_biezaca'

        Returns:
            Plotly figure
        """
        if not positions:
            fig = go.Figure()
            fig.add_annotation(
                text="Brak pozycji w portfelu",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig

        labels = [p.get('symbol', 'N/A') for p in positions]
        values = [float(p.get('wartosc_biezaca', 0) or 0) for p in positions]

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            textinfo='label+percent',
            textposition='outside',
            hovertemplate='%{label}<br>Wartość: %{value:,.2f}<br>Udział: %{percent}<extra></extra>'
        )])

        fig.update_layout(
            title=title,
            height=400,
            showlegend=True,
            legend=dict(orientation='h', yanchor='bottom', y=-0.1)
        )

        return fig

    @staticmethod
    def sector_distribution_bar(instruments: List[Dict],
                               title: str = 'Rozkład sektorowy') -> go.Figure:
        """
        Create a bar chart showing sector distribution.

        Args:
            instruments: List of instrument dicts with 'nazwa_sektora'

        Returns:
            Plotly figure
        """
        if not instruments:
            fig = go.Figure()
            fig.add_annotation(
                text="Brak danych do wyświetlenia",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig

        # Count by sector
        sector_counts = {}
        for inst in instruments:
            sector = inst.get('nazwa_sektora', 'Nieznany')
            sector_counts[sector] = sector_counts.get(sector, 0) + 1

        sectors = list(sector_counts.keys())
        counts = list(sector_counts.values())

        fig = go.Figure(data=[go.Bar(
            x=sectors,
            y=counts,
            marker_color='#1f77b4',
            text=counts,
            textposition='auto'
        )])

        fig.update_layout(
            title=title,
            xaxis_title='Sektor',
            yaxis_title='Liczba instrumentów',
            height=400
        )

        return fig

    @staticmethod
    def gain_loss_indicator(value: float, percent: float = None,
                           size: str = 'medium') -> str:
        """
        Create HTML for gain/loss indicator.

        Args:
            value: Gain/loss value
            percent: Optional percentage
            size: 'small', 'medium', or 'large'

        Returns:
            HTML string
        """
        color = '#26a69a' if value >= 0 else '#ef5350'
        arrow = '▲' if value >= 0 else '▼'
        sign = '+' if value > 0 else ''

        font_sizes = {'small': '14px', 'medium': '18px', 'large': '24px'}
        font_size = font_sizes.get(size, '18px')

        if percent is not None:
            text = f"{sign}{value:,.2f} ({sign}{percent:.2f}%)"
        else:
            text = f"{sign}{value:,.2f}"

        return f'<span style="color: {color}; font-size: {font_size};">{arrow} {text}</span>'

    @staticmethod
    def mini_sparkline(values: List[float], width: int = 100,
                      height: int = 30) -> go.Figure:
        """
        Create a mini sparkline chart.

        Args:
            values: List of numeric values
            width: Chart width in pixels
            height: Chart height in pixels

        Returns:
            Plotly figure
        """
        if not values or len(values) < 2:
            return None

        color = '#26a69a' if values[-1] >= values[0] else '#ef5350'

        fig = go.Figure(data=go.Scatter(
            y=values,
            mode='lines',
            line=dict(color=color, width=1),
            fill='tozeroy',
            fillcolor=f'rgba({31 if color == "#26a69a" else 239}, {166 if color == "#26a69a" else 83}, {154 if color == "#26a69a" else 80}, 0.2)'
        ))

        fig.update_layout(
            width=width,
            height=height,
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=False,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )

        return fig
