"""auth.py — Autenticação e gerenciamento de perfis com estética Apple-like."""
from __future__ import annotations

import streamlit as st
import bcrypt
from data.storage import get_perfis, add_perfil, update_perfil, delete_perfil

CORES_DISPONIVEIS = [
    "#0A84FF", "#30D158", "#FF9F0A", "#FF453A",
    "#BF5AF2", "#FF2D55", "#5AC8FA", "#FFD60A",
]

EMOJIS_POR_CATEGORIA: dict[str, list[str]] = {
    "Rostos": ["😀", "😎", "🤩", "🥹", "😍", "😂", "😅", "🥳", "🤔", "😇", "😏", "🫠", "🤑", "😤"],
    "Símbolos": ["👑", "💎", "🔥", "⭐", "✨", "🎯", "🏆", "💪", "🦁", "🦊", "🐼", "🦅", "💫", "🎉"],
    "Finanças": ["💰", "💸", "💳", "📈", "📊", "🏦", "💹", "💵", "💶", "💷", "🪙", "🧾", "🤑", "💲"],
    "Outros": ["🚀", "🎮", "🎸", "⚽", "🏄", "🌊", "🌈", "🍕", "🎲", "🧩", "🦋", "🌺", "🍀", "🎈"],
}

def _get_perfis() -> dict:
    if "perfis" not in st.session_state or not st.session_state.perfis:
        st.session_state.perfis = get_perfis()
    return st.session_state.perfis

def _reload_perfis() -> None:
    st.session_state.perfis = get_perfis()

def require_perfil() -> tuple[str, str]:
    if not st.session_state.get("username"):
        _show_perfil_selector()
        st.stop()
    username = st.session_state.username
    perfil = _get_perfis().get(username, {})
    return username, perfil.get("nome", username.title())

def logout() -> None:
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

def show_auth() -> None:
    _show_perfil_selector()

def _inject_css() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        header[data-testid="stHeader"] { display: none !important; }

        .stApp {
            background:
                radial-gradient(ellipse 90% 40% at 50% -2%,
                    rgba(10,132,255,0.18) 0%, transparent 65%),
                #000 !important;
            min-height: 100vh;
        }

        *, *::before, *::after {
            font-family: -apple-system, BlinkMacSystemFont,
                         "SF Pro Display", "SF Pro Text",
                         Inter, sans-serif !important;
            box-sizing: border-box;
        }

        .block-container {
            padding: 0 2rem 4rem !important;
            max-width: 860px !important;
            margin: 0 auto !important;
        }

        [data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(18,18,22,0.92) !important;
            border: 1px solid rgba(255,255,255,0.09) !important;
            border-radius: 24px !important;
            padding: 28px 28px 24px !important;
            backdrop-filter: blur(24px) !important;
            -webkit-backdrop-filter: blur(24px) !important;
            box-shadow:
                0 0 0 1px rgba(255,255,255,0.03) inset,
                0 32px 80px rgba(0,0,0,0.55) !important;
        }

        .hero {
            display: flex; flex-direction: column;
            align-items: center; text-align: center;
            padding: 60px 0 44px;
        }
        .hero-icon {
            width: 64px; height: 64px; border-radius: 20px;
            background: linear-gradient(145deg, #1A94FF, #0055CC);
            display: flex; align-items: center; justify-content: center;
            font-size: 1.8rem;
            box-shadow: 0 8px 32px rgba(10,132,255,0.45);
            margin-bottom: 24px;
        }
        .hero-eyebrow {
            font-size: 0.62rem; font-weight: 700;
            letter-spacing: 0.18em; text-transform: uppercase;
            color: rgba(235,235,245,0.28); margin-bottom: 10px;
        }
        .hero-title {
            font-size: 2.5rem; font-weight: 800; color: #fff;
            letter-spacing: -0.05em; line-height: 1.04; margin-bottom: 10px;
        }
        .hero-sub {
            font-size: 0.88rem; color: rgba(235,235,245,0.3);
            max-width: 320px; line-height: 1.6;
        }

        .pcard {
            background: rgba(26,26,30,0.9);
            border: 1.5px solid rgba(255,255,255,0.07);
            border-radius: 22px;
            padding: 26px 12px 16px;
            text-align: center;
            min-height: 156px;
            transition: transform .22s cubic-bezier(.16,1,.3,1),
                        border-color .22s ease,
                        box-shadow .22s ease,
                        background .22s ease;
            cursor: pointer;
            position: relative;
            overflow: hidden;
        }
        .pcard::after {
            content: '';
            position: absolute; inset: 0;
            background: linear-gradient(160deg, rgba(255,255,255,0.04) 0%, transparent 55%);
            border-radius: inherit; pointer-events: none;
        }
        .pcard.sel {
            border-color: #0A84FF !important;
            background: rgba(10,132,255,0.10) !important;
            box-shadow:
                0 0 0 3px rgba(10,132,255,0.22),
                0 20px 48px rgba(0,0,0,0.55) !important;
            transform: translateY(-5px) scale(1.03) !important;
        }
        .pcard.sel .pcard-name { color: #fff; }
        .pcard.sel .pcard-check { opacity: 1 !important; }

        .pcard-check {
            position: absolute; top: 10px; right: 11px;
            width: 20px; height: 20px; border-radius: 50%;
            background: #0A84FF;
            display: flex; align-items: center; justify-content: center;
            font-size: 0.58rem; color: #fff; font-weight: 900;
            opacity: 0; transition: opacity .2s ease;
        }
        .pcard-avatar {
            width: 72px; height: 72px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 2rem; color: #fff;
            margin: 0 auto 12px;
            box-shadow: 0 6px 20px rgba(0,0,0,0.45);
        }
        .pcard-name {
            font-size: 0.88rem; font-weight: 600;
            color: rgba(235,235,245,0.82);
            letter-spacing: -0.01em; margin-bottom: 2px;
        }
        .pcard-user {
            font-size: 0.65rem; color: rgba(235,235,245,0.2);
        }

        .card-sel-btn .stButton button {
            background: transparent !important;
            border: 1px solid rgba(255,255,255,0.06) !important;
            box-shadow: none !important;
            height: 32px !important; min-height: 32px !important;
            color: rgba(235,235,245,0.22) !important;
            font-size: 0.68rem !important; font-weight: 600 !important;
            letter-spacing: 0.04em !important;
            border-radius: 10px !important;
            transition: all .18s ease !important;
        }
        .card-sel-btn .stButton button:hover {
            background: rgba(10,132,255,0.13) !important;
            border-color: rgba(10,132,255,0.38) !important;
            color: #5AB0FF !important;
            transform: none !important;
            box-shadow: none !important;
        }
        .card-sel-btn .stButton button[kind="primary"] {
            background: rgba(10,132,255,0.16) !important;
            border-color: rgba(10,132,255,0.5) !important;
            color: #4DA3FF !important;
            box-shadow: none !important;
        }

        .btn-entrar .stButton button {
            background: rgba(255,255,255,0.07) !important;
            border: 1px solid rgba(255,255,255,0.13) !important;
            color: rgba(235,235,245,0.82) !important;
            font-size: 0.95rem !important; font-weight: 600 !important;
            border-radius: 16px !important;
            padding: 0.65rem 1.4rem !important;
            box-shadow: none !important;
            transition: all .22s cubic-bezier(.16,1,.3,1) !important;
            letter-spacing: -0.01em !important;
        }
        .btn-entrar .stButton button:hover {
            background: #0A84FF !important;
            border-color: transparent !important;
            color: #fff !important;
            box-shadow: 0 6px 28px rgba(10,132,255,0.48) !important;
            transform: translateY(-2px) scale(1.01) !important;
        }

        .sec-lbl {
            font-size: 0.60rem; font-weight: 700;
            letter-spacing: 0.16em; text-transform: uppercase;
            color: rgba(235,235,245,0.22); margin: 20px 0 8px;
        }
        .divider {
            height: 1px; background: rgba(255,255,255,0.05);
            margin: 22px 0;
        }

        .av-preview {
            display: flex; flex-direction: column;
            align-items: center; padding: 14px 0 6px; gap: 6px;
        }
        .av-circle {
            width: 88px; height: 88px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 2.4rem; color: #fff;
            box-shadow: 0 12px 36px rgba(0,0,0,0.55);
            border: 1.5px solid rgba(255,255,255,0.1);
            transition: background .25s ease;
        }
        .av-name  { font-size: 0.9rem; font-weight: 600; color: rgba(235,235,245,0.68); }
        .av-hint  { font-size: 0.62rem; color: rgba(235,235,245,0.18); letter-spacing: 0.06em; }

        .color-row [data-testid="column"] {
            padding: 0 3px !important;
        }
        .color-row [data-testid="column"] button {
            height: 40px !important; min-height: 40px !important;
            border-radius: 50% !important; padding: 0 !important;
            font-size: 0.78rem !important; font-weight: 900 !important;
            color: transparent !important;
            border: 2px solid rgba(255,255,255,0.0) !important;
            transition: transform .15s ease, border-color .15s ease,
                        box-shadow .15s ease !important;
        }
        .color-row [data-testid="column"] button:hover {
            transform: scale(1.15) !important;
            border-color: rgba(255,255,255,0.45) !important;
            color: transparent !important;
        }
        .color-row [data-testid="column"] button[kind="primary"] {
            color: rgba(255,255,255,0.92) !important;
            border: 2.5px solid #fff !important;
            box-shadow:
                0 0 0 3px rgba(255,255,255,0.22),
                0 4px 16px rgba(0,0,0,0.5) !important;
            transform: scale(1.12) !important;
        }

        .emoji-row [data-testid="column"] { padding: 0 2px !important; }
        .emoji-row [data-testid="column"] button {
            height: 46px !important; min-height: 46px !important;
            border-radius: 13px !important; padding: 0 !important;
            font-size: 1.45rem !important; line-height: 1 !important;
            background: rgba(255,255,255,0.04) !important;
            border: 1.5px solid rgba(255,255,255,0.06) !important;
            color: rgba(235,235,245,0.9) !important;
            transition: background .14s ease, transform .14s ease !important;
        }
        .emoji-row [data-testid="column"] button:hover {
            background: rgba(255,255,255,0.09) !important;
            transform: scale(1.1) !important;
            border-color: rgba(255,255,255,0.14) !important;
        }
        .emoji-row [data-testid="column"] button[kind="primary"] {
            background: rgba(10,132,255,0.18) !important;
            border: 1.5px solid #0A84FF !important;
            box-shadow: 0 0 14px rgba(10,132,255,0.28) !important;
        }

        [data-testid="stSegmentedControl"] {
            background: rgba(255,255,255,0.04) !important;
            border: 1px solid rgba(255,255,255,0.07) !important;
            border-radius: 12px !important; padding: 3px !important;
            margin-bottom: 12px !important;
        }
        [data-testid="stSegmentedControl"] p {
            font-size: 0.78rem !important; font-weight: 600 !important;
            color: rgba(235,235,245,0.38) !important;
        }
        [data-testid="stSegmentedControl"] [aria-selected="true"] p {
            color: #fff !important;
        }

        [data-testid="stTextInput"] label p {
            font-size: 0.62rem !important; font-weight: 700 !important;
            letter-spacing: 0.15em !important; text-transform: uppercase !important;
            color: rgba(235,235,245,0.22) !important;
        }
        [data-testid="stTextInput"] input {
            background: rgba(255,255,255,0.05) !important;
            border: 1px solid rgba(255,255,255,0.09) !important;
            border-radius: 13px !important; color: #fff !important;
            font-size: 0.95rem !important; padding: 0.65rem 1rem !important;
        }
        [data-testid="stTextInput"] input::placeholder {
            color: rgba(235,235,245,0.16) !important;
        }
        [data-testid="stTextInput"] input:focus {
            border-color: #0A84FF !important;
            box-shadow: 0 0 0 3px rgba(10,132,255,0.18) !important;
        }
        [data-testid="stSelectbox"] label p {
            font-size: 0.62rem !important; font-weight: 700 !important;
            letter-spacing: 0.15em !important; text-transform: uppercase !important;
            color: rgba(235,235,245,0.22) !important;
        }
        [data-testid="stSelectbox"] > div > div {
            background: rgba(255,255,255,0.05) !important;
            border: 1px solid rgba(255,255,255,0.09) !important;
            border-radius: 13px !important;
            color: rgba(235,235,245,0.72) !important;
        }
        [data-testid="stToggle"] p {
            color: rgba(235,235,245,0.35) !important;
            font-size: 0.84rem !important;
        }

        .stButton button {
            border-radius: 14px !important; font-weight: 600 !important;
            font-size: 0.86rem !important; padding: 0.52rem 1.2rem !important;
            border: 1px solid rgba(255,255,255,0.08) !important;
            background: rgba(28,28,30,0.9) !important;
            color: rgba(235,235,245,0.55) !important;
            transition: all .18s cubic-bezier(.16,1,.3,1) !important;
            box-shadow: 0 1px 4px rgba(0,0,0,0.3) !important;
        }
        .stButton button:hover {
            background: rgba(44,44,46,0.95) !important;
            border-color: rgba(255,255,255,0.14) !important;
            color: #fff !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 16px rgba(0,0,0,0.35) !important;
        }
        .stButton button[kind="primary"] {
            background: #0A84FF !important; border-color: transparent !important;
            color: #fff !important;
            box-shadow: 0 4px 20px rgba(10,132,255,0.38) !important;
        }
        .stButton button[kind="primary"]:hover {
            background: #0071E3 !important;
            box-shadow: 0 6px 26px rgba(10,132,255,0.5) !important;
        }

        .muted {
            font-size: 0.78rem; color: rgba(235,235,245,0.22);
            line-height: 1.55; text-align: center;
        }

        @media (max-width: 640px) {
            .hero-title { font-size: 1.9rem; }
            .block-container { padding: 0 1rem 3rem !important; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def _render_color_picker(key: str, default: str) -> str:
    sk = f"cpick_{key}"
    if sk not in st.session_state:
        st.session_state[sk] = default if default in CORES_DISPONIVEIS else CORES_DISPONIVEIS[0]
    atual = st.session_state[sk]

    cor_livre = st.color_picker(
        "Escolha uma cor personalizada",
        value=st.session_state[sk],
        key=f"native_{key}",
        label_visibility="collapsed",
    )

    if cor_livre != st.session_state[sk]:
        st.session_state[sk] = cor_livre
        st.rerun()

    return st.session_state[sk]

def _render_emoji_picker(key: str, default: str) -> str:
    sk = f"epick_{key}"
    cat_sk = f"epick_cat_{key}"
    all_em = [e for cat in EMOJIS_POR_CATEGORIA.values() for e in cat]

    if sk not in st.session_state:
        st.session_state[sk] = default if default in all_em else all_em[0]
    if cat_sk not in st.session_state:
        st.session_state[cat_sk] = list(EMOJIS_POR_CATEGORIA.keys())[0]

    cat_sel = st.segmented_control(
        "cat",
        list(EMOJIS_POR_CATEGORIA.keys()),
        key=cat_sk,
        label_visibility="collapsed",
    )
    emojis = EMOJIS_POR_CATEGORIA.get(cat_sel or list(EMOJIS_POR_CATEGORIA.keys())[0], [])
    atual = st.session_state[sk]

    per_row = 7
    st.markdown("<div class='emoji-row'>", unsafe_allow_html=True)
    for row_start in range(0, len(emojis), per_row):
        row = emojis[row_start:row_start + per_row]
        cols = st.columns(per_row, gap="small")
        for col, em in zip(cols, row):
            with col:
                if st.button(
                    em,
                    key=f"em_{key}_{em}",
                    width='stretch',
                    type="primary" if atual == em else "secondary",
                ):
                    st.session_state[sk] = em
                    st.rerun()
        for col in cols[len(row):]:
            with col:
                st.markdown("<div style='height:46px'></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    return st.session_state[sk]

def _avatar_preview(avatar: str, cor: str, nome: str = "") -> None:
    st.markdown(
        f"""
        <div class="av-preview">
            <div class="av-circle" style="background:{cor}">{avatar}</div>
            <div class="av-name">{nome or "Prévia"}</div>
            <div class="av-hint">aparência no seletor</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def _mode_selecionar() -> None:
    perfis = _get_perfis()
    items = list(perfis.items())

    st.markdown(
        """
        <div class="hero">
            <div class="hero-icon">📈</div>
            <div class="hero-eyebrow">Finanças Pessoais</div>
            <div class="hero-title">Quem está usando?</div>
            <div class="hero-sub">Selecione seu perfil para continuar.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not items:
        st.markdown(
            """
            <div style="text-align:center;padding:40px 0;
                 color:rgba(235,235,245,0.2);font-size:.88rem;line-height:1.7;">
                Nenhum perfil criado ainda.<br>Crie o seu primeiro abaixo.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        sel_key = "auth_card_sel"
        if sel_key not in st.session_state:
            st.session_state[sel_key] = items[0][0]

        per_row = min(len(items), 4)
        for row_start in range(0, len(items), per_row):
            row = items[row_start:row_start + per_row]
            cols = st.columns(len(row), gap="medium")
            for col, (username, info) in zip(cols, row):
                with col:
                    cor = info.get("cor", "#0A84FF")
                    avatar = info.get("avatar", "👤")
                    nome = info.get("nome", username)
                    is_sel = st.session_state[sel_key] == username

                    st.markdown(
                        f"""
                        <div class="pcard {'sel' if is_sel else ''}">
                            <div class="pcard-check">✓</div>
                            <div class="pcard-avatar" style="background:{cor}">{avatar}</div>
                            <div class="pcard-name">{nome}</div>
                            <div class="pcard-user">@{username}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.markdown("<div class='card-sel-btn'>", unsafe_allow_html=True)
                    if st.button(
                        "✓ Selecionado" if is_sel else "Selecionar",
                        key=f"card_{username}",
                        width='stretch',
                        type="primary" if is_sel else "secondary",
                    ):
                        st.session_state[sel_key] = username
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

        sel_username = st.session_state[sel_key]
        sel_nome = perfis.get(sel_username, {}).get("nome", sel_username)

        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
        _, btn_c, _ = st.columns([1, 1.5, 1])
        with btn_c:
            st.markdown("<div class='btn-entrar'>", unsafe_allow_html=True)
            if st.button(
                f"Entrar como {sel_nome}",
                width='stretch',
                key="btn_entrar",
            ):
                sel_info = perfis[sel_username]
                if sel_info.get("password_hash"):
                    st.session_state["auth_password_username"] = sel_username
                    st.rerun()
                else:
                    st.session_state.username = sel_username
                    st.session_state.aba = "Dashboard"
                    st.session_state.auth_mode = "selecionar"
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    if "auth_password_username" in st.session_state:
        username = st.session_state["auth_password_username"]
        info = perfis[username]
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sec-lbl'>Digite a senha para @{username}</div>", unsafe_allow_html=True)
        password_input = st.text_input("Senha", type="password", key="auth_password")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Entrar", key="btn_auth_enter"):
                if bcrypt.checkpw(password_input.encode(), info["password_hash"].encode()):
                    st.session_state.username = username
                    st.session_state.aba = "Dashboard"
                    st.session_state.auth_mode = "selecionar"
                    del st.session_state["auth_password_username"]
                    st.session_state.pop("auth_password", None)
                    st.rerun()
                else:
                    st.error("Senha incorreta.")
        with c2:
            if st.button("Voltar", key="btn_auth_back"):
                del st.session_state["auth_password_username"]
                st.session_state.pop("auth_password", None)
                st.rerun()

    st.markdown("<div class='divider' style='margin-top:28px'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.6, 1])
    with c1:
        if st.button("＋  Novo perfil", width='stretch', type="primary"):
            st.session_state.auth_mode = "adicionar"
            st.rerun()
    with c2:
        st.markdown(
            "<div class='muted' style='padding-top:10px'>"
            "Gerencie nome, avatar e cor dos seus perfis."
            "</div>",
            unsafe_allow_html=True,
        )
    with c3:
        if st.button("⚙  Gerenciar", width='stretch'):
            st.session_state.auth_mode = "gerenciar"
            st.rerun()

def _mode_adicionar() -> None:
    st.markdown(
        """
        <div class="hero" style="padding-bottom:28px">
            <div class="hero-eyebrow">Novo perfil</div>
            <div class="hero-title" style="font-size:2rem">Criar perfil</div>
            <div class="hero-sub">Personalize nome, emoji e cor.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container():
        nome = st.text_input("Nome do perfil", placeholder="Ex: Pedro", key="add_nome")
        usar_emoji = st.toggle("Usar emoji como avatar", value=True, key="add_usar_emoji")
        cor_prev = st.session_state.get("cpick_add_cor", CORES_DISPONIVEIS[0])

        if usar_emoji:
            st.markdown("<div class='sec-lbl'>Avatar</div>", unsafe_allow_html=True)
            avatar = _render_emoji_picker("add_avatar", "😀")
        else:
            avatar = nome.strip()[0].upper() if nome.strip() else "?"

        _avatar_preview(avatar, cor_prev, nome.strip())

        st.markdown("<div class='sec-lbl'>Cor</div>", unsafe_allow_html=True)
        cor = _render_color_picker("add_cor", CORES_DISPONIVEIS[0])

        st.markdown("<div class='sec-lbl'>Senha (opcional)</div>", unsafe_allow_html=True)
        password = st.text_input("Senha", type="password", key="add_password", placeholder="Deixe em branco para sem senha")

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Criar perfil", width='stretch', type="primary", key="btn_criar"):
                nome_strip = nome.strip()
                password_hash = None
                if password:
                    if len(password) < 6:
                        st.error("Senha deve ter pelo menos 6 caracteres.")
                    else:
                        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                if not nome_strip:
                    st.error("Digite um nome para o perfil.")
                elif password and len(password) < 6:
                    pass  # error already shown
                else:
                    u = nome_strip.lower().replace(" ", "_")
                    ok, err = add_perfil(u, nome_strip, avatar, cor, password_hash)
                    if ok:
                        _reload_perfis()
                        for k in ["cpick_add_cor", "epick_add_avatar", "epick_cat_add_avatar", "add_nome", "add_usar_emoji", "add_password"]:
                            st.session_state.pop(k, None)
                        st.session_state.auth_mode = "selecionar"
                        st.rerun()
                    else:
                        st.error(f"Erro: {err}")
        with c2:
            if st.button("Cancelar", width='stretch', key="btn_cancelar_add"):
                st.session_state.auth_mode = "selecionar"
                st.rerun()

def _mode_gerenciar() -> None:
    perfis = _get_perfis()

    st.markdown(
        """
        <div class="hero" style="padding-bottom:28px">
            <div class="hero-eyebrow">Gerenciar perfis</div>
            <div class="hero-title" style="font-size:2rem">Editar perfil</div>
            <div class="hero-sub">Altere nome, avatar e cor.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='form-card'>", unsafe_allow_html=True)

    if not perfis:
        st.markdown(
            "<div class='muted' style='padding:20px 0;text-align:center'>"
            "Nenhum perfil disponível.</div>",
            unsafe_allow_html=True,
        )
        if st.button("Voltar", key="btn_voltar_vazio"):
            st.session_state.auth_mode = "selecionar"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        return

    nomes = {u: info.get("nome", u) for u, info in perfis.items()}

    def _on_perfil_change():
        sel = st.session_state["ger_sel"]
        info = perfis.get(sel, {})
        all_em = [e for cat in EMOJIS_POR_CATEGORIA.values() for e in cat]
        for k in list(st.session_state.keys()):
            if k in ("ger_nome", "ger_usar_emoji", "cpick_ger_cor", "epick_ger_avatar") or \
               k.startswith("em_ger_") or \
               k.startswith("epick_cat_ger_") or \
               k.startswith("cpick_ger_"):
                del st.session_state[k]
        st.session_state["ger_nome"] = info.get("nome", sel)
        st.session_state["ger_usar_emoji"] = info.get("avatar", "") in all_em
        st.session_state["cpick_ger_cor"] = info.get("cor", CORES_DISPONIVEIS[0])
        st.session_state["epick_ger_avatar"] = info.get("avatar", "😀")

    if "ger_sel" not in st.session_state:
        primeiro = list(nomes.keys())[0]
        st.session_state["ger_sel"] = primeiro
        _on_perfil_change()

    username_sel = st.selectbox(
        "Perfil",
        list(nomes.keys()),
        format_func=lambda u: nomes[u],
        key="ger_sel",
        on_change=_on_perfil_change,
    )

    info = perfis[username_sel]
    avatar_atual = info.get("avatar", "😀")

    novo_nome = st.text_input("Nome do perfil", key="ger_nome")

    all_em = [e for cat in EMOJIS_POR_CATEGORIA.values() for e in cat]
    usar_emoji = st.toggle(
        "Usar emoji como avatar",
        key="ger_usar_emoji",
    )

    cor_preview = st.session_state.get("cpick_ger_cor", info.get("cor", CORES_DISPONIVEIS[0]))

    if usar_emoji:
        st.markdown("<div class='sec-lbl'>Avatar</div>", unsafe_allow_html=True)
        novo_avatar = _render_emoji_picker(
            "ger_avatar",
            st.session_state.get("epick_ger_avatar", avatar_atual),
        )
    else:
        novo_avatar = novo_nome.strip()[0].upper() if novo_nome.strip() else "?"

    _avatar_preview(novo_avatar, cor_preview, novo_nome.strip() or nomes[username_sel])

    st.markdown("<div class='sec-lbl'>Cor</div>", unsafe_allow_html=True)
    nova_cor = _render_color_picker("ger_cor", info.get("cor", CORES_DISPONIVEIS[0]))

    st.markdown("<div class='sec-lbl'>Senha (opcional)</div>", unsafe_allow_html=True)
    password_change = st.text_input("Nova senha", type="password", key="ger_password", placeholder="Deixe em branco para manter/sem senha")
    confirm_password = st.text_input("Confirmar nova senha", type="password", key="ger_confirm_password")

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Salvar", width='stretch', type="primary", key="btn_salvar"):
            nome_final = novo_nome.strip() or info.get("nome", username_sel)
            password_hash = info.get("password_hash", "")
            if password_change:
                if password_change != confirm_password:
                    st.error("Senhas não coincidem.")
                elif len(password_change) < 6:
                    st.error("Senha deve ter pelo menos 6 caracteres.")
                else:
                    password_hash = bcrypt.hashpw(password_change.encode(), bcrypt.gensalt()).decode()
            if password_change and (password_change != confirm_password or len(password_change) < 6):
                pass  # error already shown
            else:
                ok, err = update_perfil(username_sel, nome_final, novo_avatar, nova_cor, password_hash)
                if ok:
                    _reload_perfis()
                    for k in list(st.session_state.keys()):
                        if k.startswith("ger_") or k.startswith("cpick_ger") or k.startswith("epick_ger") or k.startswith("em_ger_"):
                            st.session_state.pop(k, None)
                    st.session_state.auth_mode = "selecionar"
                    st.rerun()
                else:
                    st.error(f"Erro: {err}")
    with c2:
        if st.button("Excluir perfil", width='stretch', key="btn_excluir"):
            if len(perfis) <= 1:
                st.error("Mantenha ao menos um perfil.")
            else:
                ok, err = delete_perfil(username_sel)
                if ok:
                    st.session_state.perfis = {k: v for k, v in perfis.items() if k != username_sel}
                    for k in list(st.session_state.keys()):
                        if k.startswith("ger_") or k.startswith("cpick_ger") or k.startswith("epick_ger") or k.startswith("em_ger_"):
                            st.session_state.pop(k, None)
                    st.session_state.auth_mode = "selecionar"
                    st.rerun()
                else:
                    st.error(f"Erro: {err}")
    with c3:
        if st.button("Voltar", width='stretch', key="btn_voltar"):
            for k in list(st.session_state.keys()):
                if k.startswith("ger_") or k.startswith("cpick_ger") or k.startswith("epick_ger") or k.startswith("em_ger_"):
                    st.session_state.pop(k, None)
            st.session_state.auth_mode = "selecionar"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

def _show_perfil_selector() -> None:
    _inject_css()
    st.session_state.setdefault("auth_mode", "selecionar")
    _, mid, _ = st.columns([0.3, 2.4, 0.3])
    with mid:
        mode = st.session_state.auth_mode
        if mode == "selecionar":
            _mode_selecionar()
        elif mode == "adicionar":
            _mode_adicionar()
        elif mode == "gerenciar":
            _mode_gerenciar()