"""app.py — Roteador principal com seleção de perfil."""
import streamlit as st
from datetime import datetime
from pathlib import Path

from auth import require_perfil, logout
from data.storage import get_perfis, get_cartoes_cfg
from utils.helpers import MESES_PT, CARTOES_CORES
from config import APP_TITULO, APP_ICONE, ANO_MINIMO

from views.dashboard import show_dashboard
from views.lancamentos import show_lancamentos
from views.ganhos import show_ganhos
from views.cartao import show_cartao
from views.extrato import show_extrato
from views.configuracoes import show_configuracoes
from views.metas import show_metas
from views.relatorio import show_relatorio
from views.importar import show_importar

st.set_page_config(
    page_title=APP_TITULO,
    page_icon=APP_ICONE,
    layout="wide",
    initial_sidebar_state="expanded",
)

_CSS_PATH = Path("assets/styles.css")
if _CSS_PATH.exists():
    st.markdown(f"<style>{_CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

_username, _user_name = require_perfil()
_perfil_info = get_perfis().get(_username, {})
_user_avatar = _perfil_info.get("avatar", _user_name[0].upper() if _user_name else "U")
_user_cor = _perfil_info.get("cor", "#0A84FF")

now = datetime.now()
ANO_NOW, MES_NOW = now.year, now.month

if "cartoes_cfg" not in st.session_state:
    _raw_cfg = get_cartoes_cfg(_username)
    st.session_state.cartoes_cfg = [
        {
            "id": int(r["id"]),
            "nome": str(r["nome"]),
            "digitos": str(r["digitos"]),
            "limite": float(r["limite"]) if str(r["limite"]).strip() else 0.0,
            "vencimento": int(r["vencimento"]) if str(r["vencimento"]).strip() else 1,
            "cor": str(r["cor"]) if r.get("cor") else "#820AD1",
        }
        for r in _raw_cfg
    ]

DEFAULTS = dict(
    aba="Dashboard",
    ano_sel=ANO_NOW,
    mes_sel=MES_NOW,
    edit_lanc=None,
    edit_ganho=None,
    edit_cartao=None,
    det_desc="",
    det_val=0.0,
)
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

_mobile_pages = [
    "Dashboard", "Ganhos", "Lancamentos", "Cartao", "Metas",
    "Importar", "Extrato", "Relatorio", "Configuracoes",
]
_mobile_index = _mobile_pages.index(st.session_state.aba) if st.session_state.aba in _mobile_pages else 0
_mobile_choice = st.selectbox("", _mobile_pages, index=_mobile_index, key="mobile_nav", label_visibility="collapsed")
if _mobile_choice != st.session_state.aba:
    st.session_state.aba = _mobile_choice
    st.rerun()

anos_disp = list(range(max(ANO_MINIMO, ANO_NOW - 5), ANO_NOW + 2))
anos_disp = sorted(set(anos_disp), reverse=True)

ano_sb = st.session_state.ano_sel
mes_max_sb = MES_NOW if ano_sb == ANO_NOW else 12
meses_disp = list(range(1, mes_max_sb + 1))

if st.session_state.mes_sel not in meses_disp:
    st.session_state.mes_sel = meses_disp[-1]

with st.sidebar:
    st.markdown(
        f"""
        <div class="sb-logo-wrap">
          <div class="sb-logo-icon">📈</div>
          <span class="sb-logo-name">{APP_TITULO}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sb-section">Menu</div>', unsafe_allow_html=True)

    def _nav_button(label: str, aba: str, key: str):
        ativo = st.session_state.aba == aba
        st.markdown(
            f'<div class="{"nav-active" if ativo else "nav-item"}">',
            unsafe_allow_html=True,
        )
        if st.button(label, key=key, width='stretch'):
            st.session_state.aba = aba
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    _nav_button("📊 Dashboard", "Dashboard", "nav_Dashboard")

    st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-section">Financeiro</div>', unsafe_allow_html=True)

    _nav_button("💰 Ganhos", "Ganhos", "nav_Ganhos")
    _nav_button("➕ Lançamentos", "Lancamentos", "nav_Lancamentos")
    _nav_button("💳 Cartão", "Cartao", "nav_Cartao")
    _nav_button("🎯 Metas", "Metas", "nav_Metas")

    st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-section">Utilidades</div>', unsafe_allow_html=True)

    _nav_button("📥 Importar", "Importar", "nav_Importar")
    _nav_button("📋 Extrato", "Extrato", "nav_Extrato")
    _nav_button("🗂️ Relatório", "Relatorio", "nav_Relatorio")
    _nav_button("⚙️ Configurações", "Configuracoes", "nav_Configuracoes")
    

    st.markdown('<div class="sb-spacer"></div>', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="sb-footer">
          <div class="sb-avatar" style="background:{_user_cor};color:#fff">{_user_avatar}</div>
          <span class="sb-footer-name">{_user_name}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")
    if st.button("🚪 Sair", key="logout_sidebar", width='stretch'):
        logout()
        st.rerun()

aba = st.session_state.aba

if aba == "Dashboard":
    show_dashboard(_username)
elif aba == "Ganhos":
    show_ganhos(_username)
elif aba == "Lancamentos":
    show_lancamentos(_username)
elif aba == "Cartao":
    show_cartao(_username)
elif aba == "Metas":
    show_metas(_username)
elif aba == "Importar":
    show_importar(_username)
elif aba == "Extrato":
    show_extrato(_username)
elif aba == "Relatorio":
    show_relatorio(_username)
elif aba == "Configuracoes":
    show_configuracoes(_username)
else:
    st.session_state.aba = "Dashboard"
    st.rerun()