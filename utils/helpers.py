"""utils/helpers.py — funções auxiliares de formatação e UI."""
from __future__ import annotations

import streamlit as st

from utils.tokens import (  # noqa: F401
    MESES_PT, MESES_ABR, CORES_CAT,
    CARTOES, CARTOES_CORES, FORMAS_PAGAMENTO,
)


# ─── Formatação monetária ──────────────────────────────────────────────────
def brl(value: float | int | None, show_sign: bool = False) -> str:
    """Formata um número como BRL. Ex: 1234.5 → 'R$ 1.234,50'."""
    if value is None:
        return "R$ —"
    prefix = "+" if show_sign and value > 0 else ""
    formatted = f"{abs(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{prefix}R$ {formatted}" if value >= 0 else f"-R$ {formatted}"


def _parse_brl(text: str) -> float:
    """Converte string BRL para float. Ex: 'R$ 1.234,50' → 1234.50."""
    s = str(text).strip().replace("R$", "").strip()
    if not s:
        return 0.0
    try:
        if "," in s and "." in s:
            return max(0.0, float(s.replace(".", "").replace(",", ".")))
        elif "," in s:
            return max(0.0, float(s.replace(",", ".")))
        return max(0.0, float(s))
    except ValueError:
        return 0.0


# ─── Feedback visual ──────────────────────────────────────────────────────
def _show_feedback() -> None:
    """Exibe mensagem de sucesso/erro armazenada em session_state e a limpa.

    Uso nas views:
        st.session_state["msgok"] = "Salvo com sucesso!"
        st.rerun()

    Na próxima execução a view chama:
        _show_feedback()   # sem argumentos

    Para exibir um feedback imediato (sem rerun), use _show_feedback_now().
    """
    msg = st.session_state.pop("msgok", None)
    if msg:
        st.success(msg)
    err = st.session_state.pop("msgerr", None)
    if err:
        st.error(err)


def _show_feedback_now(tipo: str, mensagem: str) -> None:
    """Exibe feedback imediato sem depender de session_state.

    tipo: "success" | "error" | "warning" | "info"
    """
    fn = {
        "success": st.success,
        "error":   st.error,
        "warning": st.warning,
        "info":    st.info,
    }.get(tipo, st.info)
    fn(mensagem)


# ─── Background / layout helper ───────────────────────────────────────────
def pbg(
    h: int = 220,
    xaxis: dict | None = None,
    yaxis: dict | None = None,
) -> dict:
    """Retorna dict de layout Plotly com fundo transparente.

    Mantém assinatura compatível com o uso original:
        fig.update_layout(**pbg(h=260))
    """
    _AXIS = dict(
        gridcolor="rgba(255,255,255,0.04)",
        zerolinecolor="rgba(255,255,255,0.04)",
        color="rgba(235,235,245,0.3)",
    )
    return dict(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="rgba(235,235,245,0.3)", size=10),
        margin=dict(l=6, r=6, t=6, b=20),
        height=h,
        xaxis=xaxis if xaxis is not None else _AXIS,
        yaxis=yaxis if yaxis is not None else _AXIS,
    )
