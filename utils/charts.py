"""utils/charts.py — fábrica de gráficos Plotly padronizados para o app."""
from __future__ import annotations

from typing import Sequence

import plotly.graph_objects as go

from utils.color import to_rgba
from utils.tokens import CORES, CORES_CAT

# ─── Configuração base compartilhada ──────────────────────────────────────
_AXIS_BASE = dict(
    gridcolor="rgba(255,255,255,0.04)",
    linecolor="rgba(255,255,255,0.07)",
    tickcolor="rgba(255,255,255,0.07)",
    tickfont=dict(color="rgba(235,235,245,0.18)", size=10),
    zeroline=False,
)

LAYOUT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(
        color=CORES["estrutura"],
        size=11,
        family="-apple-system, Inter, sans-serif",
    ),
    xaxis=_AXIS_BASE,
    yaxis=_AXIS_BASE,
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        bordercolor=CORES["borda"],
        borderwidth=1,
        font=dict(color="rgba(235,235,245,0.3)", size=10),
    ),
    margin=dict(l=4, r=4, t=24, b=4),
    hoverlabel=dict(
        bgcolor="#1C1C1E",
        bordercolor="rgba(255,255,255,0.1)",
        font_color="#FFFFFF",
        font_size=11,
    ),
)


def _apply_base(fig: go.Figure, h: int = 220, **extra_layout) -> go.Figure:
    """Aplica LAYOUT_BASE + extras ao figure."""
    layout = dict(LAYOUT_BASE, height=h, **extra_layout)
    fig.update_layout(**layout)
    return fig


# ─── Sparkline ─────────────────────────────────────────────────────────────
def spark(
    vals: Sequence[float],
    color: str,
    height: int = 48,
    smoothing: float = 1.1,
) -> go.Figure:
    """Sparkline de linha simples com área preenchida.

    Parâmetros
    ----------
    vals : sequência de floats
    color : cor hex ou rgba
    height : altura em px (padrão 48)
    smoothing : suavização da spline (0–1.3)
    """
    if not vals:
        vals = [0, 0]

    fig = go.Figure(
        go.Scatter(
            y=list(vals),
            mode="lines",
            line=dict(color=color, width=2, shape="spline", smoothing=smoothing),
            fill="tozeroy",
            fillcolor=to_rgba(color, 0.12),
            hoverinfo="skip",
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        height=height,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig


# ─── Barras mensais ────────────────────────────────────────────────────────
def bar_mensal(
    labels: Sequence[str],
    values: Sequence[float],
    color: str = CORES["secundario"],
    height: int = 220,
    title: str = "",
) -> go.Figure:
    """Gráfico de barras mensais simples."""
    fig = go.Figure(
        go.Bar(
            x=list(labels),
            y=list(values),
            marker_color=color,
            marker_line_width=0,
        )
    )
    _apply_base(fig, h=height, title=dict(text=title, font=dict(size=12)) if title else {})
    return fig


def bar_agrupado(
    labels: Sequence[str],
    series: dict[str, Sequence[float]],
    colors: Sequence[str] | None = None,
    height: int = 240,
    title: str = "",
) -> go.Figure:
    """Barras agrupadas. `series` = {nome: [valores]}."""
    _colors = colors or CORES_CAT
    fig = go.Figure()
    for i, (nome, vals) in enumerate(series.items()):
        fig.add_trace(
            go.Bar(
                name=nome,
                x=list(labels),
                y=list(vals),
                marker_color=_colors[i % len(_colors)],
                marker_line_width=0,
            )
        )
    fig.update_layout(barmode="group")
    _apply_base(fig, h=height, title=dict(text=title, font=dict(size=12)) if title else {})
    return fig


# ─── Donut ─────────────────────────────────────────────────────────────────
def donut(
    labels: Sequence[str],
    values: Sequence[float],
    colors: Sequence[str] | None = None,
    height: int = 240,
    hole: float = 0.6,
    title: str = "",
) -> go.Figure:
    """Gráfico de rosca."""
    _colors = list(colors) if colors else CORES_CAT[: len(labels)]
    fig = go.Figure(
        go.Pie(
            labels=list(labels),
            values=list(values),
            hole=hole,
            marker=dict(colors=_colors, line=dict(color="rgba(0,0,0,0)", width=0)),
            textinfo="percent",
            textfont=dict(size=11, color="rgba(235,235,245,0.7)"),
            hovertemplate="%{label}: %{value:,.2f}<extra></extra>",
        )
    )
    _apply_base(
        fig,
        h=height,
        showlegend=True,
        title=dict(text=title, font=dict(size=12)) if title else {},
    )
    return fig


# ─── Linha acumulada ───────────────────────────────────────────────────────
def linha_acumulada(
    x: Sequence,
    y: Sequence[float],
    color: str = CORES["positivo"],
    height: int = 220,
    name: str = "",
    fill: bool = True,
) -> go.Figure:
    """Gráfico de linha simples com área opcional."""
    fig = go.Figure(
        go.Scatter(
            x=list(x),
            y=list(y),
            mode="lines",
            name=name,
            line=dict(color=color, width=2, shape="spline", smoothing=0.8),
            fill="tozeroy" if fill else "none",
            fillcolor=to_rgba(color, 0.1),
            hovertemplate="%{y:,.2f}<extra></extra>",
        )
    )
    _apply_base(fig, h=height)
    return fig


def multi_linha(
    x: Sequence,
    series: dict[str, Sequence[float]],
    colors: Sequence[str] | None = None,
    height: int = 240,
    title: str = "",
) -> go.Figure:
    """Múltiplas linhas no mesmo gráfico. `series` = {nome: [valores]}."""
    _colors = colors or CORES_CAT
    fig = go.Figure()
    for i, (nome, vals) in enumerate(series.items()):
        fig.add_trace(
            go.Scatter(
                x=list(x),
                y=list(vals),
                mode="lines",
                name=nome,
                line=dict(color=_colors[i % len(_colors)], width=2, shape="spline"),
                hovertemplate=f"{nome}: %{{y:,.2f}}<extra></extra>",
            )
        )
    _apply_base(fig, h=height, title=dict(text=title, font=dict(size=12)) if title else {})
    return fig
