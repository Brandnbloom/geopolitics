"""
geo_impact.py - Sector, commodity, and correlation analytics
"""

import pandas as pd
import plotly.graph_objects as go
from config import SECTORS, SECTOR_ICONS, COMMODITIES


def build_sector_heatmap(sector_df: pd.DataFrame) -> go.Figure:
    """Build a sector impact heatmap over time."""
    if sector_df.empty:
        return go.Figure()

    z = sector_df.values.clip(-4, 4)
    labels = sector_df.index.tolist()
    col_labels = [c if i % 3 == 0 else "" for i, c in enumerate(sector_df.columns.tolist())]

    custom_text = []
    for i, sector in enumerate(labels):
        row_text = []
        for j, month in enumerate(sector_df.columns):
            val = sector_df.iloc[i, j]
            if val > 0:
                msg = f"<b>{sector}</b><br>{month}<br>Impact: +{val:.0f} (POSITIVE)<br>Geopolitical events drove demand"
            elif val < 0:
                msg = f"<b>{sector}</b><br>{month}<br>Impact: {val:.0f} (NEGATIVE)<br>Events disrupted this sector"
            else:
                msg = f"<b>{sector}</b><br>{month}<br>Neutral - no major event impact"
            row_text.append(msg)
        custom_text.append(row_text)

    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=col_labels,
        y=labels,
        customdata=custom_text,
        hovertemplate="%{customdata}<extra></extra>",
        colorscale=[
            [0.0,  "#FF3B5B"],
            [0.35, "#8B1A2A"],
            [0.5,  "#1A2236"],
            [0.65, "#0D4A2A"],
            [1.0,  "#00E5A0"],
        ],
        zmid=0, zmin=-4, zmax=4,
        showscale=True,
        colorbar=dict(
            title=dict(text="Impact Score", font=dict(color="#8B99B5")),
            tickfont=dict(color="#8B99B5"),
            bgcolor="#111827",
            bordercolor="#1E2D45",
            len=0.8,
        ),
    ))

    fig.update_layout(
        title=dict(
            text="Sector Impact Heatmap — Geopolitical Events Feb 2022 → Present",
            font=dict(color="#F0F4FF", size=15),
        ),
        plot_bgcolor="#0A0E1A",
        paper_bgcolor="#0A0E1A",
        font=dict(color="#8B99B5"),
        xaxis=dict(tickfont=dict(color="#8B99B5", size=9), showgrid=False, title=""),
        yaxis=dict(tickfont=dict(color="#F0F4FF", size=12), showgrid=False),
        margin=dict(l=20, r=20, t=50, b=30),
        height=360,
    )
    return fig


def build_commodity_heatmap(commodity_df: pd.DataFrame) -> go.Figure:
    """Build daily commodity % change heatmap."""
    if commodity_df.empty:
        return go.Figure()

    df = commodity_df.tail(20).T
    z = df.values
    dates = [str(d)[:10] for d in df.columns]
    short_dates = [d[5:] for d in dates]

    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=short_dates,
        y=df.index.tolist(),
        hovertemplate="<b>%{y}</b><br>Date: %{x}<br>Daily Change: %{z:.2f}%<extra></extra>",
        colorscale=[
            [0.0, "#FF3B5B"],
            [0.4, "#6B1D2A"],
            [0.5, "#1A2236"],
            [0.6, "#0D4A2A"],
            [1.0, "#00E5A0"],
        ],
        zmid=0,
        showscale=True,
        colorbar=dict(
            title=dict(text="Daily %", font=dict(color="#8B99B5")),
            tickfont=dict(color="#8B99B5"),
            bgcolor="#111827",
            bordercolor="#1E2D45",
        ),
    ))

    fig.update_layout(
        title=dict(
            text="🔥 Commodity Daily % Change — Last 20 Trading Days",
            font=dict(color="#F0F4FF", size=15),
        ),
        plot_bgcolor="#0A0E1A",
        paper_bgcolor="#0A0E1A",
        font=dict(color="#8B99B5"),
        xaxis=dict(tickfont=dict(color="#8B99B5", size=9), showgrid=False),
        yaxis=dict(tickfont=dict(color="#F0F4FF", size=12), showgrid=False),
        margin=dict(l=20, r=20, t=50, b=40),
        height=280,
    )
    return fig


def build_correlation_matrix(corr_df: pd.DataFrame) -> go.Figure:
    """Build an asset return correlation matrix heatmap."""
    if corr_df.empty:
        return go.Figure()

    fig = go.Figure(data=go.Heatmap(
        z=corr_df.values,
        x=corr_df.columns.tolist(),
        y=corr_df.index.tolist(),
        hovertemplate="<b>%{y}</b> vs <b>%{x}</b><br>Correlation: %{z:.2f}<extra></extra>",
        colorscale=[
            [0.0,  "#FF3B5B"],
            [0.45, "#1A2236"],
            [0.5,  "#111827"],
            [0.55, "#0D4A2A"],
            [1.0,  "#00E5A0"],
        ],
        zmid=0, zmin=-1, zmax=1,
        showscale=True,
        text=corr_df.values.round(2),
        texttemplate="%{text}",
        textfont=dict(size=8, color="#8B99B5"),
        colorbar=dict(
            title=dict(text="Correlation", font=dict(color="#8B99B5")),
            tickfont=dict(color="#8B99B5"),
            bgcolor="#111827",
            bordercolor="#1E2D45",
        ),
    ))

    fig.update_layout(
        title=dict(
            text="📊 Asset Return Correlation Matrix",
            font=dict(color="#F0F4FF", size=15),
        ),
        plot_bgcolor="#0A0E1A",
        paper_bgcolor="#0A0E1A",
        font=dict(color="#8B99B5"),
        xaxis=dict(tickfont=dict(color="#8B99B5", size=9), tickangle=-45, showgrid=False),
        yaxis=dict(tickfont=dict(color="#8B99B5", size=9), showgrid=False),
        margin=dict(l=20, r=20, t=50, b=80),
        height=500,
    )
    return fig


def build_cumulative_returns_chart(cum_returns_df: pd.DataFrame, selected_assets: list) -> go.Figure:
    """Build cumulative returns line chart for selected assets."""
    if cum_returns_df.empty:
        return go.Figure()

    available = [a for a in selected_assets if a in cum_returns_df.columns]
    if not available:
        available = cum_returns_df.columns[:6].tolist()

    PALETTE = [
        "#3B82F6", "#00E5A0", "#FF3B5B", "#FFD700",
        "#FF8C42", "#A78BFA", "#F472B6", "#34D399",
        "#60A5FA", "#FCA5A5", "#86EFAC", "#FDE68A",
    ]

    fig = go.Figure()
    for i, asset in enumerate(available):
        fig.add_trace(go.Scatter(
            x=cum_returns_df.index,
            y=cum_returns_df[asset],
            name=asset,
            line=dict(color=PALETTE[i % len(PALETTE)], width=2),
            hovertemplate=(
                f"<b>{asset}</b><br>"
                "Date: %{x|%b %d, %Y}<br>"
                "Index: %{y:.1f}<br>"
                "<extra></extra>"
            ),
        ))

    fig.add_hline(
        y=100, line_dash="dot", line_color="#1E2D45",
        annotation_text="War Start (Feb 24, 2022)",
        annotation_font_color="#8B99B5",
        annotation_font_size=10,
    )

    fig.update_layout(
        title=dict(
            text="📈 Cumulative Returns — Indexed to 100 at War Start (Feb 24, 2022)",
            font=dict(color="#F0F4FF", size=15),
        ),
        plot_bgcolor="#0A0E1A",
        paper_bgcolor="#0A0E1A",
        font=dict(color="#8B99B5"),
        xaxis=dict(
            showgrid=True, gridcolor="#1E2D45", gridwidth=0.5,
            tickfont=dict(color="#8B99B5"),
            rangeslider=dict(visible=True, bgcolor="#111827", bordercolor="#1E2D45"),
        ),
        yaxis=dict(
            showgrid=True, gridcolor="#1E2D45", gridwidth=0.5,
            tickfont=dict(color="#8B99B5"),
            title=dict(text="Index (100 = Feb 24, 2022)", font=dict(color="#8B99B5")),
        ),
        legend=dict(
            font=dict(color="#8B99B5", size=10),
            bgcolor="#111827",
            bordercolor="#1E2D45",
            orientation="h",
            yanchor="bottom", y=-0.35,
            xanchor="center", x=0.5,
        ),
        margin=dict(l=20, r=20, t=50, b=100),
        height=480,
        hovermode="x unified",
    )
    return fig