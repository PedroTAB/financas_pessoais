"""utils/styles.py — carregador de CSS externo."""
from __future__ import annotations

from pathlib import Path

import streamlit as st

_CSS_FILE = Path(__file__).parent.parent / "utils" / "styles.css"


def load_css(path: str | Path | None = None) -> str:
    """Lê o arquivo CSS e retorna seu conteúdo como string.

    Se `path` não for informado, usa utils/styles.css por padrão.
    Retorna string vazia se o arquivo não existir (não quebra o app).
    """
    target = Path(path) if path else _CSS_FILE
    if not target.exists():
        return ""
    return target.read_text(encoding="utf-8")


def inject_css(path: str | Path | None = None) -> None:
    """Injeta o CSS no Streamlit via st.markdown."""
    css = load_css(path)
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
