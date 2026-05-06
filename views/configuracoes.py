"""views/configuracoes.py — Configurações do usuário."""
from __future__ import annotations

import streamlit as st
import pandas as pd
import bcrypt

from data.storage import (
    get_categories, add_category, remove_category,
    get_user_config, save_user_config,
    registrar_historico, get_historico,
    get_perfis, update_perfil,
    CATEGORIAS_DEBITO, CATEGORIAS_CREDITO,
)
from utils.helpers import brl, _show_feedback
from utils.tokens import CORES


def show_configuracoes(username: str = "") -> None:
    _show_feedback()

    st.markdown("""
        <div class="dash-header">
            <div class="dash-title">Configurações</div>
            <div class="dash-subtitle">Personalize categorias e regras do seu orçamento</div>
        </div>
    """, unsafe_allow_html=True)

    tab_cat, tab_orc, tab_hist, tab_senha = st.tabs(
        ["📂 Categorias", "📊 Orçamento 50/30/20", "🕓 Histórico", "🔐 Senha"]
    )

    with tab_cat:
        _tab_categorias(username)

    with tab_orc:
        _tab_orcamento(username)

    with tab_hist:
        _tab_historico(username)

    with tab_senha:
        _tab_senha(username)


# ─── Aba: Categorias ──────────────────────────────────────────────────────

def _tab_categorias(username: str) -> None:
    st.markdown("##### 🔴 Categorias de Débito")
    _render_cat_section(username, "debito", CATEGORIAS_DEBITO)
    st.markdown("---")
    st.markdown("##### 🟢 Categorias de Crédito")
    _render_cat_section(username, "credito", CATEGORIAS_CREDITO)


def _render_cat_section(username: str, tipo: str, padrao: list) -> None:
    cats = get_categories(username)
    lista = cats.get(tipo, [])
    padrao_set = set(padrao)

    cols = st.columns(4)
    for i, cat in enumerate(lista):
        with cols[i % 4]:
            if cat in padrao_set:
                st.markdown(
                    f'<div class="dtag" title="Padrão — protegida">🔒 {cat}</div>',
                    unsafe_allow_html=True,
                )
            else:
                if st.button(
                    f"✕  {cat}",
                    key=f"rmcat_{tipo}_{cat}",
                    help="Clique para remover",
                    width='stretch',
                ):
                    ok = remove_category(username, tipo, cat)
                    st.session_state["msgok" if ok else "msgerr"] = (
                        f"Categoria '{cat}' removida." if ok
                        else f"Não foi possível remover '{cat}'."
                    )
                    st.rerun()

    st.markdown("")
    with st.form(f"form_cat_{tipo}", clear_on_submit=True):
        nova = st.text_input(
            "Nova categoria",
            placeholder="Farmácia" if tipo == "debito" else "Freelance",
        )
        if st.form_submit_button("➕ Adicionar", width='stretch'):
            if not nova.strip():
                st.error("Digite um nome.")
            else:
                ok = add_category(username, tipo, nova.strip())
                st.session_state["msgok" if ok else "msgerr"] = (
                    f"'{nova.strip()}' adicionada!" if ok
                    else f"'{nova.strip()}' já existe ou é inválida."
                )
                st.rerun()


# ─── Aba: Orçamento ───────────────────────────────────────────────────────

def _calc_poupanca(nec: int, des: int) -> int:
    return max(0, 100 - int(nec) - int(des))


def _recalc_orcamento_state(username: str):
    nec = int(st.session_state.get("cfg_nec", 50))
    des = int(st.session_state.get("cfg_des", 30))

    if nec + des > 100:
        excesso = nec + des - 100
        if st.session_state.get("_cfg_last_changed") == "cfg_nec":
            des = max(0, des - excesso)
            st.session_state.cfg_des = des
        else:
            nec = max(0, nec - excesso)
            st.session_state.cfg_nec = nec

    pou = _calc_poupanca(nec, des)
    st.session_state.cfg_calc = {
        "necessidades": nec,
        "desejos": des,
        "poupanca": pou,
    }


def _on_change_nec(username: str):
    st.session_state._cfg_last_changed = "cfg_nec"
    _recalc_orcamento_state(username)


def _on_change_des(username: str):
    st.session_state._cfg_last_changed = "cfg_des"
    _recalc_orcamento_state(username)


def _get_renda_liquida_mes(username: str, ano: int, mes: int) -> float:
    from data.storage import get_ganhos
    dfg = get_ganhos(username)
    if dfg is None or dfg.empty:
        return 0.0
    dfm = dfg[(dfg["ano"] == int(ano)) & (dfg["mes"] == int(mes))].copy()
    if dfm.empty or "valor_liquido" not in dfm.columns:
        return 0.0
    return float(pd.to_numeric(dfm["valor_liquido"], errors="coerce").fillna(0).sum())


def _tab_orcamento(username: str) -> None:
    from datetime import datetime

    now = datetime.now()
    ANO_NOW, MES_NOW = now.year, now.month

    cfg = get_user_config(username)
    nec_ini = int(cfg.get("necessidades", 50))
    des_ini = int(cfg.get("desejos", 30))
    pou_ini = int(cfg.get("poupanca", 100 - nec_ini - des_ini))

    if "cfg_nec" not in st.session_state:
        st.session_state.cfg_nec = nec_ini
    if "cfg_des" not in st.session_state:
        st.session_state.cfg_des = des_ini
    if "cfg_calc" not in st.session_state:
        st.session_state.cfg_calc = {
            "necessidades": nec_ini,
            "desejos": des_ini,
            "poupanca": pou_ini,
        }

    st.markdown("Defina como distribuir sua renda entre necessidades, desejos e poupança.")
    st.markdown("")

    c1, c2 = st.columns([1.2, 1])

    with c1:
        st.markdown("##### 🎚️ Ajuste de percentuais")

        st.slider(
            "🏠 Necessidades (%)",
            min_value=0,
            max_value=100,
            key="cfg_nec",
            on_change=_on_change_nec,
            args=(username,),
        )

        st.slider(
            "🎯 Desejos (%)",
            min_value=0,
            max_value=100,
            key="cfg_des",
            on_change=_on_change_des,
            args=(username,),
        )

        cfg_live = st.session_state.get("cfg_calc", {})
        nec = int(cfg_live.get("necessidades", st.session_state.cfg_nec))
        des = int(cfg_live.get("desejos", st.session_state.cfg_des))
        pou = int(cfg_live.get("poupanca", _calc_poupanca(nec, des)))

        cor = CORES["positivo"] if pou >= 10 else CORES["negativo"]
        aviso = "✅ Recomendado (≥10%)" if pou >= 10 else "⚠️ Abaixo do ideal"
        st.markdown(
            f"""
            <div style="padding:16px;background:#1C1C1E;border-radius:12px;
                        border:0.5px solid rgba(255,255,255,0.08);text-align:center">
                <div style="font-size:.68rem;color:rgba(235,235,245,0.35);
                            text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px">
                    💰 Poupança (auto)
                </div>
                <div style="font-size:2.4rem;font-weight:700;color:{cor};line-height:1">{pou}%</div>
                <div style="font-size:.72rem;color:rgba(235,235,245,0.3);margin-top:6px">{aviso}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        total = nec + des + pou
        if total != 100:
            st.error(f"A soma precisa fechar em 100%. Atual: {total}%")
        else:
            if st.button("💾 Salvar configuração", width='stretch'):
                try:
                    save_user_config(username, {"necessidades": nec, "desejos": des, "poupanca": pou})
                    st.session_state["msgok"] = f"Orçamento salvo: {nec}% / {des}% / {pou}%"
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

    with c2:
        st.markdown("##### 💰 Simulador de renda mensal")

        ano_sel = st.selectbox(
            "Ano",
            options=list(range(2025, ANO_NOW + 1)),
            index=list(range(2025, ANO_NOW + 1)).index(ANO_NOW),
            key="cfg_ano_sim",
        )

        mes_sel = st.selectbox(
            "Mês",
            options=list(range(1, 13)),
            index=MES_NOW - 1,
            format_func=lambda x: [
                "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
                "Jul", "Ago", "Set", "Out", "Nov", "Dez"
            ][x - 1],
            key="cfg_mes_sim",
        )

        renda_liquida = _get_renda_liquida_mes(username, ano_sel, mes_sel)

        nec_val = renda_liquida * (nec / 100)
        des_val = renda_liquida * (des / 100)
        pou_val = renda_liquida * (pou / 100)

        st.metric("Renda líquida base", brl(renda_liquida))
        st.metric("🏠 Necessidades", brl(nec_val), f"{nec}%")
        st.metric("🎯 Desejos", brl(des_val), f"{des}%")
        st.metric("💰 Poupança", brl(pou_val), f"{pou}%")

        if renda_liquida <= 0:
            st.caption("Nenhum ganho líquido encontrado para o período selecionado.")


# ─── Aba: Histórico ───────────────────────────────────────────────────────

_ICONS = {"create": "🟢", "update": "🟡", "delete": "🔴"}
_OPS   = {"create": "Criado", "update": "Editado", "delete": "Excluído"}
_ENTS  = {"lancamento": "Lançamento", "ganho": "Ganho", "cartao_compra": "Compra Cartão"}

def registrar_historico(user_id: str, entidade: str, operacao: str, registro_id: int, snapshot: dict) -> None:
    try:
        username = _safe_username(user_id)
        recs = _cached_records("historico") or []
        ids = [int(r.get("id", 0) or 0) for r in recs]
        nid = max(ids, default=0) + 1

        snap = snapshot or {}
        entidade = str(entidade or "")

        if entidade == "ganho":
            snap = {
                "tipo_ganho": snap.get("tipo_ganho", ""),
                "descricao": snap.get("descricao", ""),
                "valor_liquido": snap.get("valor_liquido", ""),
                "extras": snap.get("extras", {}),
            }
        elif entidade == "cartao_compra":
            snap = {
                "cartao": snap.get("cartao", ""),
                "descricao": snap.get("descricao", ""),
                "categoria": snap.get("categoria", ""),
                "valor_total": snap.get("valor_total", ""),
                "num_parcelas": snap.get("num_parcelas", ""),
                "ano_inicio": snap.get("ano_inicio", ""),
                "mes_inicio": snap.get("mes_inicio", ""),
                "data_registro": snap.get("data_registro", ""),
            }
        elif entidade == "cartao_config":
            snap = {
                "nome": snap.get("nome", ""),
                "digitos": snap.get("digitos", ""),
                "limite": snap.get("limite", ""),
                "vencimento": snap.get("vencimento", ""),
                "cor": snap.get("cor", ""),
            }
        elif entidade == "lancamento":
            snap = {
                "descricao": snap.get("descricao", ""),
                "categoria": snap.get("categoria", ""),
                "tipo": snap.get("tipo", ""),
                "forma_pagamento": snap.get("forma_pagamento", ""),
                "valor": snap.get("valor", ""),
                "ano": snap.get("ano", ""),
                "mes": snap.get("mes", ""),
            }

        _wshist().append_row(
            [
                nid,
                username,
                datetime.now().isoformat(timespec="seconds"),
                entidade,
                operacao,
                int(registro_id),
                json.dumps(snap, ensure_ascii=False),
            ],
            value_input_option="RAW",
        )
        _cached_records.clear()
    except Exception:
        pass


def _tab_historico(username: str) -> None:
    hist = get_historico(username, limit=200)

    if not hist:
        st.markdown(
            '<div style="text-align:center;padding:48px 0;color:rgba(235,235,245,0.3)">'
            "Nenhum evento registrado ainda.<br>"
            "<small>O histórico é preenchido ao editar ou excluir registros.</small>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    def _hist_desc_valor(entidade: str, snap: dict):
        entidade = str(entidade or "")
        snap = snap or {}

        if entidade == "lancamento":
            return snap.get("descricao", ""), snap.get("valor")
        if entidade == "ganho":
            return snap.get("descricao", "") or snap.get("tipo_ganho", ""), snap.get("valor_liquido")
        if entidade == "cartao_compra":
            return snap.get("descricao", ""), snap.get("valor_total")
        if entidade == "cartao_config":
            desc = f"{snap.get('nome', '')} · {snap.get('digitos', '')}".strip(" ·")
            return desc, snap.get("limite")
        return "", None

    f1, f2 = st.columns(2)
    with f1:
        ents_disp = sorted({h["entidade"] for h in hist})
        ent_fil = st.selectbox("Entidade", ["Todas"] + ents_disp, key="hist_ent")
    with f2:
        ops_disp = sorted({h["operacao"] for h in hist})
        op_fil = st.selectbox("Operação", ["Todas"] + ops_disp, key="hist_op")

    filtrado = [
        h for h in hist
        if (ent_fil == "Todas" or h["entidade"] == ent_fil)
        and (op_fil == "Todas" or h["operacao"] == op_fil)
    ]

    for h in filtrado[:50]:
        icone = _ICONS.get(h["operacao"], "⚪")
        op_label = _OPS.get(h["operacao"], h["operacao"])
        ent_label = _ENTS.get(h["entidade"], h["entidade"])
        ts = h["timestamp"].replace("T", " ")
        snap = h.get("snapshot", {}) or {}

        desc, valor_raw = _hist_desc_valor(h["entidade"], snap)
        valor_fmt = brl(float(valor_raw)) if valor_raw not in (None, "") else ""

        st.markdown(
            f"""
            <div style="display:grid;grid-template-columns:28px 1fr auto;gap:10px;
                        align-items:center;padding:9px 14px;margin-bottom:4px;
                        background:#1C1C1E;border-radius:10px;
                        border:0.5px solid rgba(255,255,255,0.06)">
                <div style="font-size:1.1rem;text-align:center">{icone}</div>
                <div>
                    <div style="font-size:.82rem;color:rgba(235,235,245,0.75)">
                        <strong>{op_label}</strong> · {ent_label} #{h['id']}
                        {f' — {desc}' if desc else ''}
                    </div>
                    <div style="font-size:.7rem;color:rgba(235,235,245,0.3);margin-top:2px">{ts}</div>
                </div>
                <div style="font-size:.82rem;font-weight:600;color:rgba(235,235,245,0.45);
                            font-variant-numeric:tabular-nums;text-align:right">{valor_fmt}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if len(filtrado) > 50:
        st.caption(f"Exibindo 50 de {len(filtrado)} eventos.")


# ─── Aba: Senha ───────────────────────────────────────────────────────────

def _tab_senha(username: str) -> None:
    perfis = get_perfis()
    info = perfis.get(username, {})
    has_password = bool(info.get("password_hash"))

    st.markdown("##### 🔐 Gerenciar senha")
    st.markdown(f"**Status atual:** {'Senha definida' if has_password else 'Sem senha'}")
    st.markdown("")

    password_change = st.text_input("Nova senha", type="password", key="cfg_password", placeholder="Deixe em branco para remover senha")
    confirm_password = st.text_input("Confirmar nova senha", type="password", key="cfg_confirm_password")

    if st.button("💾 Salvar senha", width='stretch'):
        if password_change:
            if password_change != confirm_password:
                st.error("Senhas não coincidem.")
            elif len(password_change) < 6:
                st.error("Senha deve ter pelo menos 6 caracteres.")
            else:
                password_hash = bcrypt.hashpw(password_change.encode(), bcrypt.gensalt()).decode()
                ok, err = update_perfil(username, info.get("nome"), info.get("avatar"), info.get("cor"), password_hash)
                if ok:
                    st.success("Senha alterada com sucesso!")
                    st.session_state.pop("cfg_password", None)
                    st.session_state.pop("cfg_confirm_password", None)
                    st.rerun()
                else:
                    st.error(f"Erro: {err}")
        else:
            # Remove password
            ok, err = update_perfil(username, info.get("nome"), info.get("avatar"), info.get("cor"), "")
            if ok:
                st.success("Senha removida com sucesso!")
                st.session_state.pop("cfg_password", None)
                st.session_state.pop("cfg_confirm_password", None)
                st.rerun()
            else:
                st.error(f"Erro: {err}")