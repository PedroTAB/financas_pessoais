"""views/extrato.py - Extrato."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from utils.color import to_rgba
from utils.charts import spark, bar_mensal, donut, linha_acumulada
from utils.helpers import (
    brl, MESES_PT,
)
from config import (
    ANO_MINIMO,
)
from data.storage import (
    get_lancamentos, get_ganhos, get_cartao_compras,
    get_parcelas_mes, get_total_cartao_mes,
    CATEGORIAS,
)

now = datetime.now()
ANO_NOW, MES_NOW = now.year, now.month


def show_extrato(username: str = ""):
    # ── Dados base ───────────────────────────────────────────────────────────
    df_all    = get_lancamentos(username)
    df_ganho  = get_ganhos(username)
    df_cartao = get_cartao_compras(username)
    ANO = st.session_state.get("ano_sel", ANO_NOW)

    st.markdown("### 📋 Extrato")

    anos_ext = sorted({a for a in
        (df_all["ano"].unique().tolist()    if not df_all.empty   else []) +
        (df_ganho["ano"].unique().tolist()  if not df_ganho.empty else []) +
        [ANO_NOW] if ANO_MINIMO <= a <= ANO_NOW}, reverse=True)

    ef1,ef2,ef3,ef4 = st.columns(4)
    with ef1:
        ano_ext = st.selectbox("Ano", anos_ext,
            index=anos_ext.index(ANO) if ANO in anos_ext else 0, format_func=str)

    dfe = df_all[df_all["ano"]==ano_ext].copy()    if not df_all.empty   else df_all.copy()
    dge = df_ganho[df_ganho["ano"]==ano_ext].copy() if not df_ganho.empty else df_ganho.copy()
    meses_ex = sorted({
        *(dfe["mes"].tolist() if not dfe.empty else []),
        *(dge["mes"].tolist() if not dge.empty else [])})
    opts_mes = ["Todos"] + [MESES_PT[m] for m in meses_ex]

    with ef2:
        f_mes = st.multiselect("Mês", opts_mes[1:], default=[], placeholder="Selecione 1 ou mais")
    with ef3:
        f_tipo = st.multiselect("Tipo", ["Entrada","Saída","Cartão","Ganho"], default=[], placeholder="Selecione 1 ou mais")
    with ef4:
        f_cat = st.multiselect("Categoria", CATEGORIAS, default=[], placeholder="Selecione 1 ou mais")

    if f_mes:
        meses_sel = [k for k,v in MESES_PT.items() if v in f_mes]
        dfe = dfe[dfe["mes"].isin(meses_sel)]
        dge = dge[dge["mes"].isin(meses_sel)]
    if f_tipo:
        _tipo_map = {"Entrada": "Crédito", "Saída": "Débito"}
        tipos_lanc = [_tipo_map[t] for t in f_tipo if t in _tipo_map]
        incluir_ganhos = "Ganho" in f_tipo
        incluir_cartao = "Cartão" in f_tipo
        if tipos_lanc:
            dfe = dfe[dfe["tipo"].isin(tipos_lanc)]
        else:
            dfe = dfe.iloc[0:0]
        if not incluir_ganhos:
            dge = dge.iloc[0:0]
    if f_cat:
        dfe = dfe[dfe["categoria"].isin(f_cat)]
    dfe = dfe.sort_values(["mes","categoria"])

    st.divider()
    me1,me2,me3,me4,me5 = st.columns(5)
    tg = dge["valor_liquido"].sum()
    tc = dfe[dfe["tipo"]=="Crédito"]["valor"].sum()
    td = dfe[dfe["tipo"]=="Débito"]["valor"].sum()
    _meses_ext_sel = [k for k,v in MESES_PT.items() if v in f_mes] if f_mes else list(range(1,13))
    _tc_ext = sum(get_total_cartao_mes(df_cartao, ano_ext, m) for m in _meses_ext_sel)
    me1.metric("Ganhos líquidos", brl(tg))
    me2.metric("Entradas",        brl(tc))
    me3.metric("Saídas",          brl(td))
    me4.metric("Cartão",          brl(_tc_ext))
    me5.metric("Saldo",           brl(tg + tc - td - _tc_ext))

    st.markdown("<br>", unsafe_allow_html=True)
    _ECOLS = ["mes","descricao","categoria","tipo","valor","detalhes"]

    # ── Lançamentos ──
    ext_lanc = pd.DataFrame(columns=_ECOLS)
    if not dfe.empty:
        _el = dfe.copy()
        _el["valor"]    = _el.apply(lambda r: ("+ " if r["tipo"] == "Crédito" else "- ") + brl(r["valor"]), axis=1)
        _el["tipo"]     = _el["tipo"].map({"Crédito": "Entrada", "Débito": "Saída"}).fillna(_el["tipo"])
        _el["detalhes"] = _el["forma_pagamento"].fillna("").apply(lambda v: str(v) if str(v).strip() else "—")
        ext_lanc = _el[_ECOLS].copy()

    # ── Ganhos ──
    ext_g = pd.DataFrame(columns=_ECOLS)
    if not dge.empty:
        _eg = dge.copy()
        _eg["categoria"] = "Ganhos"
        _eg["tipo"]      = "Ganho"
        _eg["valor"]     = _eg["valor_liquido"].apply(lambda v: "+ " + brl(v))
        _eg["detalhes"]  = _eg["tipo_ganho"].fillna("").astype(str)
        ext_g = _eg[_ECOLS].copy()

    # ── Parcelas de cartão ──
    ext_cart = pd.DataFrame(columns=_ECOLS)
    if not f_tipo or "Cartão" in f_tipo:
        _frames_c = [get_parcelas_mes(df_cartao, ano_ext, m) for m in _meses_ext_sel]
        _parc_ext = pd.concat([f for f in _frames_c if not f.empty], ignore_index=True) if any(not f.empty for f in _frames_c) else pd.DataFrame()
        if not _parc_ext.empty:
            # Reconstruir o mês real de cada parcela a partir do índice do loop
            _mes_real = []
            for _pa, _pm in [(ano_ext, m) for m in _meses_ext_sel]:
                _pf = get_parcelas_mes(df_cartao, _pa, _pm)
                if not _pf.empty:
                    _mes_real.extend([_pm] * len(_pf))
            if len(_mes_real) != len(_parc_ext):
                _mes_real = [ano_ext] * len(_parc_ext)  # fallback seguro
            ext_cart = pd.DataFrame({
                "mes":      _mes_real,
                "descricao": _parc_ext.apply(lambda r: f"{r['descricao']} ({int(r['parcela_atual'])}/{int(r['total_parcelas'])})", axis=1),
                "categoria": _parc_ext["categoria"],
                "tipo":      "Cartão",
                "valor":     _parc_ext["valor_parcela"].apply(lambda v: f"- {brl(v)}"),
                "detalhes":  _parc_ext["cartao"].astype(str),
            })

    extrato_show = pd.concat([ext_lanc, ext_g, ext_cart], ignore_index=True)

    if not extrato_show.empty:
        extrato_show["mes_num"] = pd.to_numeric(extrato_show["mes"], errors="coerce").fillna(0).astype(int)
        extrato_show = extrato_show.sort_values(["mes_num","categoria","tipo","descricao"]).drop(columns=["mes_num"])
        extrato_show["mes"] = extrato_show["mes"].apply(lambda m: MESES_PT.get(int(m), str(m)) if str(m).isdigit() else str(m))
        extrato_show.columns = ["Mês","Descrição","Categoria","Tipo","Valor","Detalhes"]
        st.dataframe(extrato_show, width='stretch', hide_index=True)
        csv = extrato_show.to_csv(index=False).encode()
        st.download_button("⬇️ Baixar CSV", csv, f"extrato_{ano_ext}.csv", "text/csv")
    else:
        st.info("Nenhum registro com esses filtros.")
