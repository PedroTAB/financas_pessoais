"""views/dashboard.py - Dashboard."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from utils.color import to_rgba
from utils.charts import spark, bar_mensal, donut, linha_acumulada
from utils.helpers import (
    brl, _parse_brl, pbg, _show_feedback,
    MESES_PT, MESES_ABR, CORES_CAT,
    CARTOES, CARTOES_CORES, FORMAS_PAGAMENTO,
)
from config import (
    USUARIO_NOME, USUARIO_AVATAR, APP_TITULO, APP_ICONE,
    LIMITE_NECESSIDADES, LIMITE_DESEJOS, LIMITE_POUPANCA,
    CATEGORIAS_NECESSIDADES, CATEGORIAS_DESEJOS, ANO_MINIMO,
)
from data.storage import (
    get_lancamentos, add_lancamento, update_lancamento, delete_lancamento,
    get_ganhos, add_ganho, update_ganho, delete_ganho,
    get_cartao_compras, add_cartao_compra, update_cartao_compra, delete_cartao_compra,
    get_parcelas_mes, get_total_cartao_mes, get_projecao_cartao,
    get_cartoes_cfg, add_cartao_cfg, delete_cartao_cfg,
    get_user_config,
    calc_inss, calc_irrf,
    CATEGORIAS, CATEGORIAS_DEBITO, CATEGORIAS_CREDITO,
    TIPOS, TIPOS_GANHO, TIPOS_INV,
    INSS_FAIXAS, INSS_TETO, IRRF_FAIXAS, IRRF_DED_DEP, _cached_records,
)

now = datetime.now()
ANO_NOW, MES_NOW = now.year, now.month




def show_dashboard(username: str):
    # ── Patch multi-usuário ───────────────────────────────────────────────
    import functools as _ft
    from data import storage as _st
    get_lancamentos     = _ft.partial(_st.get_lancamentos, username)
    add_lancamento      = _ft.partial(_st.add_lancamento, username)
    update_lancamento   = _ft.partial(_st.update_lancamento, username)
    delete_lancamento   = _ft.partial(_st.delete_lancamento, username)
    get_ganhos          = _ft.partial(_st.get_ganhos, username)
    add_ganho           = _ft.partial(_st.add_ganho, username)
    update_ganho        = _ft.partial(_st.update_ganho, username)
    delete_ganho        = _ft.partial(_st.delete_ganho, username)
    get_cartao_compras  = _ft.partial(_st.get_cartao_compras, username)
    add_cartao_compra   = _ft.partial(_st.add_cartao_compra, username)
    update_cartao_compra= _ft.partial(_st.update_cartao_compra, username)
    delete_cartao_compra= _ft.partial(_st.delete_cartao_compra, username)
    get_cartoes_cfg     = _ft.partial(_st.get_cartoes_cfg, username)
    add_cartao_cfg      = _ft.partial(_st.add_cartao_cfg, username)
    delete_cartao_cfg   = _ft.partial(_st.delete_cartao_cfg, username)
    # ─────────────────────────────────────────────────────────────────────

    # ── Carregar dados ────────────────────────────────────────────────────────
    df_all    = get_lancamentos()
    df_ganho  = get_ganhos()
    df_cartao = get_cartao_compras()

    # ════════════════════════════════════════════════════════════════
    # DADOS — filtros e cálculos
    # ════════════════════════════════════════════════════════════════
    _anos_com_dados = sorted({
            *(df_all["ano"].tolist()   if not df_all.empty   else []),
            *(df_ganho["ano"].tolist() if not df_ganho.empty else []),
        }, reverse=True) or [ANO_NOW]
    _todos_meses_com_dados = sorted({
        *(df_all["mes"].tolist()   if not df_all.empty   else []),
        *(df_ganho["mes"].tolist() if not df_ganho.empty else []),
    }) or [MES_NOW]

    if "dash_anos_sel" not in st.session_state:
        st.session_state.dash_anos_sel = [ANO_NOW]
    if "dash_meses_sel" not in st.session_state:
        st.session_state.dash_meses_sel = [MES_NOW]

    # ─── SEÇÃO 0 — Header + filtros ──────────────────────────────────────────
    _h1, _h2, _h3 = st.columns([2.5, 1.5, 1.5])
    with _h1:
        st.markdown("""
            <div class='dash-header'>
                <div class='dash-title'>📊 Dashboard</div>
                <div class='dash-subtitle'>Visão geral das finanças</div>
            </div>""", unsafe_allow_html=True)
    with _h2:
        anos_ms = st.multiselect("Ano", options=_anos_com_dados,
            default=[a for a in st.session_state.dash_anos_sel if a in _anos_com_dados] or [_anos_com_dados[0]],
            format_func=str, key="dash_anos_ms", placeholder="Selecione ano(s)")
        if not anos_ms: anos_ms = [_anos_com_dados[0]]
        st.session_state.dash_anos_sel = anos_ms
    with _h3:
        meses_ms = st.multiselect("Mês", options=_todos_meses_com_dados,
            default=[m for m in st.session_state.dash_meses_sel if m in _todos_meses_com_dados] or [_todos_meses_com_dados[-1]],
            format_func=lambda x: MESES_PT[x], key="dash_meses_ms", placeholder="Selecione mês(es)")
        if not meses_ms: meses_ms = [_todos_meses_com_dados[-1]]
        st.session_state.dash_meses_sel = meses_ms

    ANO = anos_ms[0]; MES = meses_ms[0]
    st.session_state.ano_sel = ANO; st.session_state.mes_sel = MES

    _df_dash     = df_all[df_all["ano"].isin(anos_ms) & df_all["mes"].isin(meses_ms)].copy() if not df_all.empty else df_all.copy()
    _dg_dash     = df_ganho[df_ganho["ano"].isin(anos_ms) & df_ganho["mes"].isin(meses_ms)].copy() if not df_ganho.empty else df_ganho.copy()
    _df_dash_ano = df_all[df_all["ano"].isin(anos_ms)].copy() if not df_all.empty else df_all.copy()
    _dg_dash_ano = df_ganho[df_ganho["ano"].isin(anos_ms)].copy() if not df_ganho.empty else df_ganho.copy()

    _parc_mes = get_parcelas_mes(df_cartao, ANO, MES)
    _cart_ms = float(_parc_mes["valor_parcela"].sum()) if not _parc_mes.empty else 0.0
    _cart_ano_m = [get_total_cartao_mes(df_cartao, ANO, m) for m in range(1, 13)]
    _cart_ano = sum(_cart_ano_m)

    _cred_ms  = _df_dash[_df_dash["tipo"]=="Crédito"]["valor"].sum() if not _df_dash.empty else 0.0
    _cred_ano = _df_dash_ano[_df_dash_ano["tipo"]=="Crédito"]["valor"].sum() if not _df_dash_ano.empty else 0.0
    _deb_ms   = _df_dash[_df_dash["tipo"]=="Débito"]["valor"].sum() if not _df_dash.empty else 0.0
    _deb_ano  = _df_dash_ano[_df_dash_ano["tipo"]=="Débito"]["valor"].sum() if not _df_dash_ano.empty else 0.0

    _rec_ms      = (_dg_dash["valor_liquido"].sum() if not _dg_dash.empty else 0.0) + _cred_ms
    _rec_ano_ms  = (_dg_dash_ano["valor_liquido"].sum() if not _dg_dash_ano.empty else 0.0) + _cred_ano
    _saidas_ms   = _deb_ms + _cart_ms
    _saidas_ano  = _deb_ano + _cart_ano
    _saldo_ms    = _rec_ms - _saidas_ms
    _saldo_acum  = _rec_ano_ms - _saidas_ano

    mrl = list(range(1, 13))
    _spark_x = [MESES_ABR[m] for m in mrl]
    ganho_m = [_dg_dash_ano[_dg_dash_ano["mes"]==m]["valor_liquido"].sum() if not _dg_dash_ano.empty else 0.0 for m in mrl]
    cred_m  = [_df_dash_ano[(_df_dash_ano["mes"]==m) & (_df_dash_ano["tipo"]=="Crédito")]["valor"].sum() if not _df_dash_ano.empty else 0.0 for m in mrl]
    rec_m   = [ganho_m[i] + cred_m[i] for i in range(12)]
    deb_m   = [_df_dash_ano[(_df_dash_ano["mes"]==m) & (_df_dash_ano["tipo"]=="Débito")]["valor"].sum() if not _df_dash_ano.empty else 0.0 for m in mrl]
    saidas_m = [deb_m[i] + _cart_ano_m[i] for i in range(12)]
    saldo_m  = [rec_m[i] - saidas_m[i] for i in range(12)]

    def _spark(vals, color, height=52):
        import plotly.graph_objects as go
        to_rgba(color, alpha=0.06)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(len(vals))), y=vals, mode="lines",
            line=dict(color=color, width=2, shape="spline", smoothing=1.1),
            fill="tozeroy", fillcolor=to_rgba(color), hoverinfo="skip"
        ))
        fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), height=height,
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          xaxis=dict(visible=False), yaxis=dict(visible=False), showlegend=False)
        return fig

    # ── estilos visão geral ──────────────────────────────────────────────────
    st.markdown("""<style>
    .vg-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:4px}
    .vg-card{background:#1C1C1E;border:0.5px solid rgba(255,255,255,0.08);
        border-radius:16px;padding:18px 18px 10px;position:relative;overflow:hidden;box-shadow:0 0 0 0.5px rgba(255,255,255,0.04) inset}
    .vg-card-accent{position:absolute;top:0;left:0;right:0;height:3px;border-radius:16px 14px 0 0}
    .vg-lbl{font-size:.68rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;
        color:rgba(235,235,245,0.3);margin-bottom:8px}
    .vg-val{font-size:1.55rem;font-weight:800;letter-spacing:-0.04em;line-height:1;margin-bottom:4px;font-feature-settings:"tnum"}
    .vg-sub{font-size:.75rem;color:rgba(235,235,245,0.3);margin-bottom:10px}
    .vg-delta{display:inline-flex;align-items:center;gap:4px;font-size:.75rem;font-weight:600;
        padding:2px 8px;border-radius:999px;margin-bottom:10px}
    .vg-delta.up{background:rgba(48,209,88,0.15);color:#30D158;border:0.5px solid rgba(48,209,88,0.2)}
    .vg-delta.down{background:rgba(255,69,58,0.15);color:#FF453A;border:0.5px solid rgba(255,69,58,0.2)}
    .vg-delta.neutral{background:rgba(142,142,147,0.15);color:rgba(235,235,245,0.6);border:0.5px solid rgba(142,142,147,0.2)}
    .ux-section-card{background:#1C1C1E;border:0.5px solid rgba(255,255,255,0.08);border-radius:18px;padding:16px 18px 14px 18px;box-shadow:0 10px 30px rgba(0,0,0,0.25);margin-bottom:10px}
    .ux-section-sub{font-size:.84rem;color:rgba(235,235,245,0.6);margin:-2px 0 10px 0}
    .ux-chart-card{background:#1C1C1E;border:0.5px solid rgba(255,255,255,0.08);border-radius:16px;padding:14px 14px 6px 14px;height:100%}
    .ux-insight{background:#1C1C1E;border:1px solid rgba(142,142,147,.18);border-radius:18px;padding:16px 18px}
    .ux-kpi-note{font-size:.8rem;color:rgba(235,235,245,0.6);margin-top:6px}
    </style>""", unsafe_allow_html=True)

    def _vg_card(col, title, value, sub, acum_lbl, acum_val, color, spark_vals, delta_txt, delta_cls, icon):
        with col:
            st.markdown(f"""<div class='vg-card'>
                <div class='vg-card-accent' style='background:{color}'></div>
                <div class='vg-lbl'>{icon} {title}</div>
                <div class='vg-val' style='color:{color}'>{value}</div>
                <div class='vg-sub'>{sub}</div>
                <div class='vg-delta {delta_cls}'>{delta_txt}</div>
            </div>""", unsafe_allow_html=True)
            if spark_vals:
                _sfig = _spark(spark_vals, 'rgba(235,235,245,0.3)', height=48)
                st.plotly_chart(_sfig, width='stretch', config={"displayModeBar": False},
                key=f"vgcard_{title.replace(' ','_')}")
            st.markdown(f"""<div style='display:flex;justify-content:space-between;
                align-items:center;padding:6px 0 2px;border-top:1px solid rgba(255,255,255,0.06);
                font-size:.72rem;color:rgba(235,235,245,0.3)'>
                <span>{acum_lbl}</span>
                <span style='color:rgba(235,235,245,0.6);font-weight:600'>{acum_val}</span>
            </div>""", unsafe_allow_html=True)

    _saldo_delta_cls = "up" if _saldo_ms >= 0 else "down"
    _saldo_delta_txt = ("▲ Superávit" if _saldo_ms >= 0 else "▼ Déficit") + f" de {brl(abs(_saldo_ms))}"
    _cart_pct = (_cart_ms / _saidas_ms * 100) if _saidas_ms > 0 else 0

    st.markdown("<div class='section-label'>VISÃO GERAL</div>", unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4, gap="medium")
    _vg_card(k1, "Entradas", brl(_rec_ms), f"{len(meses_ms)} mês(es) selecionado(s)",
             "Acumulado no ano", brl(_rec_ano_ms), "#30D158", rec_m,
             f"▲ {brl(_rec_ms)}", "up", "💚")
    _vg_card(k2, "Saídas", brl(_saidas_ms), f"Débitos + cartão",
             "Acumulado no ano", brl(_saidas_ano), "#FF453A", saidas_m,
             f"▼ {brl(_saidas_ms)}", "down", "🔴")
    _vg_card(k3, "Saldo", brl(_saldo_ms), f"Entradas − Saídas",
             "Saldo acumulado", brl(_saldo_acum), "#8E8E93", saldo_m,
             _saldo_delta_txt, _saldo_delta_cls, "⚖️")
    _vg_card(k4, "Fatura Cartão", brl(_cart_ms), f"{len(_parc_mes)} parcela(s) no mês",
             "Acumulado no ano", brl(_cart_ano), "#0A84FF", _cart_ano_m,
             f"{_cart_pct:.1f}% das saídas", "neutral", "💳")

    st.divider()
    st.markdown("<div class='section-label'>FLUXO DE DINHEIRO</div>", unsafe_allow_html=True)

    _dg_tipos = _dg_dash.groupby("tipo_ganho")["valor_liquido"].sum().sort_values(ascending=False) if not _dg_dash.empty else pd.Series(dtype=float)
    _ent_map = {str(k): float(v) for k, v in _dg_tipos.items()}
    if _cred_ms > 0:
        _ent_map["Créditos"] = float(_cred_ms)

    _dcat_deb = _df_dash[_df_dash["tipo"]=="Débito"].groupby("categoria")["valor"].sum() if not _df_dash.empty else pd.Series(dtype=float)
    _dcat_cart = _parc_mes.groupby("categoria")["valor_parcela"].sum() if not _parc_mes.empty else pd.Series(dtype=float)
    dcat_mes = pd.concat([_dcat_deb, _dcat_cart]).groupby(level=0).sum().sort_values(ascending=False) if (len(_dcat_deb) or len(_dcat_cart)) else pd.Series(dtype=float)

    fp_map = {}
    if not _df_dash.empty:
        _fps = _df_dash[_df_dash["tipo"]=="Débito"].copy()
        if not _fps.empty:
            _fps["forma_pagamento"] = _fps["forma_pagamento"].replace("", "Sem forma")
            fp_map.update(_fps.groupby("forma_pagamento")["valor"].sum().to_dict())
    if _cart_ms > 0:
        fp_map["Cartão"] = fp_map.get("Cartão", 0.0) + _cart_ms
    fp_series = pd.Series(fp_map).sort_values(ascending=False) if fp_map else pd.Series(dtype=float)

    # ── estilos do novo layout de fluxo ─────────────────────────────────────
    st.markdown("""<style>
    .fluxo-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px;align-items:start}
    .fluxo-card{background:#1C1C1E;border:0.5px solid rgba(255,255,255,0.08);
        border-radius:16px;padding:18px 20px 14px}
    .fluxo-card-full{background:#1C1C1E;border:0.5px solid rgba(255,255,255,0.08);
        border-radius:16px;padding:18px 20px 14px;margin-bottom:8px;margin-top:16px}
    .fluxo-header{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:14px}
    .fluxo-title{font-size:.78rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:rgba(235,235,245,0.6)}
    .fluxo-total{font-size:1.22rem;font-weight:800;letter-spacing:-.01em}
    .fluxo-total.green{color:#30D158}
    .fluxo-total.red{color:#FF453A}
    .fluxo-total.blue{color:#8E8E93}
    .fluxo-item{display:grid;grid-template-columns:130px 1fr auto auto;align-items:center;
        gap:10px;padding:7px 0;border-bottom:1px solid rgba(255,255,255,0.06)}
    .fluxo-item:last-child{border-bottom:none}
    .fluxo-item-name{display:flex;align-items:center;gap:7px;font-size:.88rem;color:rgba(235,235,245,0.7);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    .fluxo-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
    .fluxo-bar-bg{height:6px;background:rgba(255,255,255,0.08);border-radius:99px;overflow:hidden}
    .fluxo-bar-fill{height:100%;border-radius:99px;transition:width .4s ease}
    .fluxo-val{font-size:.86rem;font-weight:600;text-align:right;white-space:nowrap;min-width:90px}
    .fluxo-pct{font-size:.75rem;color:rgba(235,235,245,0.3);text-align:right;min-width:38px}
    .fluxo-sub{margin-top:4px;padding:6px 0 2px 20px;border-left:2px solid rgba(161,161,170,.15)}
    .fluxo-sub-item{display:flex;justify-content:space-between;align-items:center;
        padding:3px 0;font-size:.78rem;color:rgba(235,235,245,0.3);gap:8px}
    .fluxo-sub-item span:last-child{font-weight:500;white-space:nowrap}
    details.fluxo-acc summary{list-style:none;cursor:pointer}
    details.fluxo-acc summary::-webkit-details-marker{display:none}
    details.fluxo-acc[open] .fluxo-chevron{transform:rotate(90deg)}
    .fluxo-chevron{display:inline-block;transition:transform .2s;font-size:.7rem;color:rgba(235,235,245,0.3);margin-left:3px}
    </style>""", unsafe_allow_html=True)

    # ── Entradas + Saídas lado a lado ─────────────────────────────────────────
    fl1, fl2 = st.columns(2, gap="medium")

    with fl1:
        _tot_ent = sum(_ent_map.values()) if _ent_map else 0
        _ent_html = ""
        if _ent_map:
            for nome, val in sorted(_ent_map.items(), key=lambda x: -x[1]):
                pct = (val / _tot_ent * 100) if _tot_ent else 0
                _ent_html += f"""<div class='fluxo-item'>
                    <div class='fluxo-item-name'><span class='fluxo-dot' style='background:#30D158'></span>{nome}</div>
                    <div class='fluxo-bar-bg'><div class='fluxo-bar-fill' style='width:{pct:.1f}%;background:#30D158;opacity:.8'></div></div>
                    <div class='fluxo-val' style='color:#30D158'>{brl(val)}</div>
                    <div class='fluxo-pct'>{pct:.1f}%</div>
                </div>"""
        else:
            _ent_html = "<div style='color:rgba(235,235,245,0.3);font-size:.85rem;padding:8px 0'>Sem entradas no período</div>"
        st.markdown(f"""<div class='fluxo-card'>
            <div class='fluxo-header'>
                <div>
                    <div class='fluxo-title'>💚 Entradas por tipo</div>
                    <div style='font-size:.75rem;color:rgba(235,235,245,0.3);margin-top:2px'>De onde veio o dinheiro</div>
                </div>
                <div class='fluxo-total green'>{brl(_tot_ent)}</div>
            </div>
            {_ent_html}
        </div>""", unsafe_allow_html=True)

    with fl2:
        _tot_sai = float(dcat_mes.sum()) if not dcat_mes.empty else 0
        _sai_html = ""
        if not dcat_mes.empty:
            _parc_cat_det_all = _parc_mes.copy() if not _parc_mes.empty else pd.DataFrame()
            for i, (cat, val) in enumerate(dcat_mes.items()):
                pct = (val / _tot_sai * 100) if _tot_sai else 0
                clr = CORES_CAT[i % len(CORES_CAT)]
                _cat_descs = {}
                _df_cat_det = _df_dash[(_df_dash["tipo"]=="Débito") & (_df_dash["categoria"]==cat)].copy() if not _df_dash.empty else pd.DataFrame()
                if not _df_cat_det.empty:
                    for _, r in _df_cat_det.iterrows():
                        fp = str(r.get("forma_pagamento","")).strip() or "Sem forma"
                        desc = f"{str(r.get('descricao','')).strip() or cat} · {fp}"
                        _cat_descs[desc] = _cat_descs.get(desc, 0) + float(r.get("valor", 0))
                if not _parc_cat_det_all.empty:
                    _pdet = _parc_cat_det_all[_parc_cat_det_all["categoria"]==cat]
                    for _, r in _pdet.iterrows():
                        desc = f"{str(r.get('descricao','')).strip() or cat} · Cartão · {str(r.get('cartao',''))} ({int(r.get('parcela_atual',0))}/{int(r.get('total_parcelas',0))})"
                        _cat_descs[desc] = _cat_descs.get(desc, 0) + float(r.get("valor_parcela", 0))
                _item_inner = f"""<div class='fluxo-item'>
                    <div class='fluxo-item-name'><span class='fluxo-dot' style='background:{clr}'></span>{cat}</div>
                    <div class='fluxo-bar-bg'><div class='fluxo-bar-fill' style='width:{pct:.1f}%;background:{clr};opacity:.8'></div></div>
                    <div class='fluxo-val' style='color:{clr}'>{brl(val)}</div>
                    <div class='fluxo-pct'>{pct:.1f}%</div>
                </div>"""
                if len(_cat_descs) > 1:
                    _sub = "".join(
                        f"<div class='fluxo-sub-item'><span>{d}</span><span style='color:{clr}'>{brl(v)}</span></div>"
                        for d, v in sorted(_cat_descs.items(), key=lambda x: -x[1])
                    )
                    _sai_html += f"""<details class='fluxo-acc'>
                        <summary>{_item_inner.replace("</div>", "<span class='fluxo-chevron'>›</span></div>", 1)}</summary>
                        <div class='fluxo-sub'>{_sub}</div>
                    </details>"""
                else:
                    _sai_html += _item_inner
        else:
            _sai_html = "<div style='color:rgba(235,235,245,0.3);font-size:.85rem;padding:8px 0'>Sem saídas no período</div>"
        st.markdown(f"""<div class='fluxo-card'>
            <div class='fluxo-header'>
                <div>
                    <div class='fluxo-title'>🔴 Saídas por categoria</div>
                    <div style='font-size:.75rem;color:rgba(235,235,245,0.3);margin-top:2px'>Para onde o dinheiro foi</div>
                </div>
                <div class='fluxo-total red'>{brl(_tot_sai)}</div>
            </div>
            {_sai_html}
        </div>""", unsafe_allow_html=True)

    # ── Forma de pagamento — card full width ──────────────────────────────────
    _tot_fp = float(fp_series.sum()) if not fp_series.empty else 0
    _fp_cols = ["#8E8E93","#0A84FF","#30D158","rgba(235,235,245,0.3)","#FF453A","#FB923C","#E879F9"]
    _fp_html = ""
    if not fp_series.empty:
        _fp_items = list(fp_series.items())
        _col_count = min(len(_fp_items), 4)
        _fp_rows = ""
        for i, (nome, val) in enumerate(_fp_items):
            pct = (float(val) / _tot_fp * 100) if _tot_fp else 0
            clr = _fp_cols[i % len(_fp_cols)]
            _fp_rows += f"""<div class='fluxo-item'>
                <div class='fluxo-item-name'><span class='fluxo-dot' style='background:{clr}'></span>{nome}</div>
                <div class='fluxo-bar-bg'><div class='fluxo-bar-fill' style='width:{pct:.1f}%;background:{clr};opacity:.8'></div></div>
                <div class='fluxo-val' style='color:{clr}'>{brl(val)}</div>
                <div class='fluxo-pct'>{pct:.1f}%</div>
            </div>"""
        _fp_html = _fp_rows
    else:
        _fp_html = "<div style='color:rgba(235,235,245,0.3);font-size:.85rem;padding:8px 0'>Sem dados no período</div>"

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.markdown(f"""<div class='fluxo-card-full'>
        <div class='fluxo-header'>
            <div>
                <div class='fluxo-title'>💳 Forma de pagamento</div>
                <div style='font-size:.75rem;color:rgba(235,235,245,0.3);margin-top:2px'>Como as saídas foram liquidadas</div>
            </div>
            <div class='fluxo-total blue'>{brl(_tot_fp)}</div>
        </div>
        {_fp_html}
    </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("<div class='section-label'>CAPACIDADE DE GASTO</div>", unsafe_allow_html=True)

    _rec_ref = _rec_ms if _rec_ms > 0 else (_rec_ano_ms / max(len(meses_ms), 1) if len(meses_ms) else 0)
    _necessidades_cats = {"Moradia","Subsistência","Transporte","Saúde","Conta","Educação","Pets"}
    _desejos_cats = {"Lazer","Vestuário","Streaming","Eletrônicos","Restaurantes","Viagem","Assinaturas","Presentes"}

    _cat_all = {}
    for cat, val in dcat_mes.items():
        _cat_all[str(cat)] = float(val)
    _gast_nec = sum(v for k, v in _cat_all.items() if k in _necessidades_cats)
    _gast_des = sum(v for k, v in _cat_all.items() if k in _desejos_cats)
    _gast_out = sum(v for k, v in _cat_all.items() if k not in _necessidades_cats and k not in _desejos_cats)
    _gast_nec += _gast_out

    # Ler percentuais configurados pelo usuário
    _cfg_user = get_user_config(username)
    _pct_nec = float(_cfg_user.get("necessidades", 50)) / 100
    _pct_des = float(_cfg_user.get("desejos", 30)) / 100
    _pct_pou = float(_cfg_user.get("poupanca", 20)) / 100

    _lim_nec = _rec_ref * _pct_nec
    _lim_des = _rec_ref * _pct_des
    _lim_pou = _rec_ref * _pct_pou
    _rest_nec = _lim_nec - _gast_nec
    _rest_des = _lim_des - _gast_des
    _poup_atual = max(_rec_ref - (_gast_nec + _gast_des), 0)
    _rest_pou = _poup_atual - _lim_pou

    from datetime import date as _date
    import calendar as _calendar
    _today = _date.today()
    _dias_mes = _calendar.monthrange(ANO, MES)[1]
    _dias_rest = max(_dias_mes - (_today.day if ANO == _today.year and MES == _today.month else 0), 1)
    _cap_dia_des = max(_rest_des, 0) / _dias_rest if _dias_rest else 0
    _cap_dia_nec = max(_rest_nec, 0) / _dias_rest if _dias_rest else 0

    # ── estilos capacidade de gasto ─────────────────────────────────────────
    st.markdown("""<style>
    .cap-grid{display:grid;grid-template-columns:1fr 2fr;gap:16px;align-items:stretch}
    .cap-summary{background:#1C1C1E;border:0.5px solid rgba(255,255,255,0.08);
        border-radius:16px;padding:22px 22px;display:flex;flex-direction:column;justify-content:center;gap:6px}
    .cap-summary-lbl{font-size:.72rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:rgba(235,235,245,0.3)}
    .cap-summary-val{font-size:2rem;font-weight:800;color:#FFFFFF;letter-spacing:-.04em;line-height:1.1;font-feature-settings:"tnum"}
    .cap-summary-sub{font-size:.8rem;color:rgba(235,235,245,0.3);line-height:1.6;margin-top:4px}
    .cap-summary-diario{margin-top:10px;padding-top:10px;border-top:1px solid rgba(161,161,170,.1)}
    .cap-summary-diario-lbl{font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;color:rgba(235,235,245,0.3);margin-bottom:6px}
    .cap-diario-item{display:flex;justify-content:space-between;align-items:center;margin-bottom:3px}
    .cap-diario-item span:first-child{font-size:.78rem;color:rgba(235,235,245,0.6)}
    .cap-diario-item span:last-child{font-size:.82rem;font-weight:600;color:#FFFFFF}
    .cap-bars{background:#1C1C1E;border:0.5px solid rgba(255,255,255,0.08);
        border-radius:16px;padding:20px 22px}
    .cap-bar-item{margin-bottom:18px}
    .cap-bar-item:last-child{margin-bottom:0}
    .cap-bar-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}
    .cap-bar-name{font-size:.88rem;font-weight:700;color:#FFFFFF}
    .cap-bar-vals{display:flex;align-items:center;gap:10px}
    .cap-bar-gasto{font-size:.82rem;color:rgba(235,235,245,0.6)}
    .cap-bar-rest{font-size:.8rem;font-weight:600;padding:2px 8px;border-radius:999px}
    .cap-bar-rest.ok{background:rgba(48,209,88,0.15);color:#30D158}
    .cap-bar-rest.over{background:rgba(255,69,58,0.15);color:#FF453A}
    .cap-bar-bg{height:8px;background:rgba(255,255,255,0.08);border-radius:999px;overflow:hidden;position:relative}
    .cap-bar-fill{height:100%;border-radius:999px;transition:width .6s cubic-bezier(0.16,1,0.3,1)}
    .cap-bar-limit{position:absolute;right:0;top:-3px;bottom:-3px;width:2px;background:rgba(255,255,255,.15);border-radius:1px}
    </style>""", unsafe_allow_html=True)

    _cap_rest_total = max(_rest_des, 0) + max(_rest_nec, 0)
    _cor_rest_total = "#30D158" if _cap_rest_total > 0 else "#FF453A"

    def _budget_block_html(nome, gasto, limite, cor, inverter_logica=False):
        gasto    = max(gasto, 0)
        pct      = (gasto / limite * 100) if limite > 0 else 0
        pctw     = max(0, min(pct, 100))
        restante = limite - gasto
        if inverter_logica:
            # Para poupança: exceder a meta é positivo
            lbl_rest = f"{'Excedente' if restante <= 0 else 'Abaixo da meta'}: {brl(abs(restante))}"
            cls_rest = "ok" if restante <= 0 else "over"
        else:
            lbl_rest = f"{'Restante' if restante >= 0 else 'Excedido'}: {brl(abs(restante))}"
            cls_rest = "ok" if restante >= 0 else "over"
        return f"""<div class='cap-bar-item'>
            <div class='cap-bar-header'>
                <div class='cap-bar-name'>{nome}</div>
                <div class='cap-bar-vals'>
                    <span class='cap-bar-gasto'>{brl(gasto)} / {brl(limite)}</span>
                    <span class='cap-bar-rest {cls_rest}'>{lbl_rest}</span>
                </div>
            </div>
            <div class='cap-bar-bg'>
                <div class='cap-bar-fill' style='width:{pctw:.1f}%;background:{cor}'></div>
            </div>
        </div>"""

    _bars_html = (
        _budget_block_html(f"Necessidades · {_cfg_user.get('necessidades', 50)}%", _gast_nec, _lim_nec, "#8E8E93") +
        _budget_block_html(f"Desejos · {_cfg_user.get('desejos', 30)}%", _gast_des, _lim_des, "#0A84FF") +
        _budget_block_html(f"Poupança · {_cfg_user.get('poupanca', 20)}%", _poup_atual, _lim_pou, "#30D158", inverter_logica=True)
    )

    st.markdown(f"""<div class='cap-grid'>
        <div class='cap-summary'>
            <div class='cap-summary-lbl'>Capacidade restante</div>
            <div class='cap-summary-val' style='color:{_cor_rest_total}'>{brl(_cap_rest_total)}</div>
            <div class='cap-summary-sub'>
                <span style='color:#0A84FF'>Desejos: {brl(max(_rest_des,0))}</span><br>
                <span style='color:#8E8E93'>Necessidades: {brl(max(_rest_nec,0))}</span><br>
                <span style='color:#30D158'>Poupança projetada: {brl(_poup_atual)}</span>
            </div>
            <div class='cap-summary-diario'>
                <div class='cap-summary-diario-lbl'>Capacidade diária</div>
                <div class='cap-diario-item'><span>Desejos</span><span>{brl(_cap_dia_des)}/dia</span></div>
                <div class='cap-diario-item'><span>Necessidades</span><span>{brl(_cap_dia_nec)}/dia</span></div>
            </div>
        </div>
        <div class='cap-bars'>{_bars_html}</div>
    </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("<div class='section-label'>TENDÊNCIAS DO ANO</div>", unsafe_allow_html=True)

    # ── KPIs anuais ──────────────────────────────────────────────────────────
    _rec_ano_total  = sum(rec_m)
    _sai_ano_total  = sum(saidas_m)
    _sal_ano_total  = sum(saldo_m)
    _melhor_mes_i   = saldo_m.index(max(saldo_m))
    _pior_mes_i     = saldo_m.index(min(saldo_m))
    _sal_cor        = "#30D158" if _sal_ano_total >= 0 else "#FF453A"
    _meses_pos      = sum(1 for v in saldo_m if v > 0)

    st.markdown("""<style>
    .tend-kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px}
    .tend-kpi{background:#1C1C1E;border:0.5px solid rgba(255,255,255,0.08);
        border-radius:16px;padding:14px 16px}
    .tend-kpi-lbl{font-size:.7rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:rgba(235,235,245,0.3);margin-bottom:4px}
    .tend-kpi-val{font-size:1.18rem;font-weight:800;letter-spacing:-0.04em;color:#FFFFFF;font-feature-settings:"tnum"}
    .tend-kpi-sub{font-size:.75rem;color:rgba(235,235,245,0.3);margin-top:3px}
    .tend-charts{display:grid;grid-template-columns:1fr 1fr;gap:16px}
    .tend-chart-card{background:#1C1C1E;border:0.5px solid rgba(255,255,255,0.08);
        border-radius:16px;padding:18px 18px 10px}
    .tend-chart-header{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:4px}
    .tend-chart-title{font-size:.78rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:rgba(235,235,245,0.6)}
    .tend-chart-badge{font-size:.75rem;font-weight:600;padding:2px 9px;border-radius:999px}
    .tend-chart-badge.green{background:rgba(48,209,88,0.15);color:#30D158}
    .tend-chart-badge.red{background:rgba(255,69,58,0.15);color:#FF453A}
    .tend-chart-badge.neutral{background:rgba(142,142,147,0.12);color:rgba(235,235,245,0.5);border:0.5px solid rgba(142,142,147,0.18)}
    .tend-chart-sub{font-size:.75rem;color:rgba(235,235,245,0.3);margin-bottom:10px}
    /* ── Lançamentos page ── */
    .lanc-page-header{display:flex;align-items:flex-start;justify-content:space-between;
        margin-bottom:20px;padding-bottom:16px;border-bottom:1px solid rgba(161,161,170,.1)}
    .lanc-page-title{font-size:1.5rem;font-weight:800;color:#FFFFFF;letter-spacing:-.02em;line-height:1.1}
    .lanc-page-sub{font-size:.82rem;color:rgba(235,235,245,0.3);margin-top:4px}
    .lanc-tipo-badge{display:inline-flex;align-items:center;gap:5px;font-size:.7rem;
        font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:3px 10px;
        border-radius:999px;margin-bottom:10px}
    .lanc-tipo-debito{background:rgba(224,92,92,.1);color:#FF453A}
    .lanc-tipo-credito{background:rgba(48,209,88,0.15);color:#30D158}
    .lanc-list-header{display:flex;align-items:center;justify-content:space-between;
        padding:.5rem 0 .6rem;margin-bottom:.4rem}
    .lanc-list-title{font-size:.72rem;font-weight:700;letter-spacing:.1em;
        text-transform:uppercase;color:rgba(235,235,245,0.3)}
    .lanc-list-totals{display:flex;gap:16px;font-size:.8rem}
    .lanc-tot-cred{color:#30D158;font-weight:600;font-variant-numeric:tabular-nums}
    .lanc-tot-deb{color:#FF453A;font-weight:600;font-variant-numeric:tabular-nums}
    .lanc-empty{text-align:center;padding:32px 0;color:rgba(235,235,245,0.3);font-size:.88rem}
    </style>""", unsafe_allow_html=True)

    st.markdown(f"""<div class='tend-kpis'>
        <div class='tend-kpi'>
            <div class='tend-kpi-lbl'>💚 Total de entradas</div>
            <div class='tend-kpi-val' style='color:#30D158'>{brl(_rec_ano_total)}</div>
            <div class='tend-kpi-sub'>Acumulado em {ANO}</div>
        </div>
        <div class='tend-kpi'>
            <div class='tend-kpi-lbl'>🔴 Total de saídas</div>
            <div class='tend-kpi-val' style='color:#FF453A'>{brl(_sai_ano_total)}</div>
            <div class='tend-kpi-sub'>Acumulado em {ANO}</div>
        </div>
        <div class='tend-kpi'>
            <div class='tend-kpi-lbl'>⚖️ Saldo acumulado</div>
            <div class='tend-kpi-val' style='color:{_sal_cor}'>{brl(_sal_ano_total)}</div>
            <div class='tend-kpi-sub'>{"Superávit" if _sal_ano_total >= 0 else "Déficit"} no ano</div>
        </div>
        <div class='tend-kpi'>
            <div class='tend-kpi-lbl'>📅 Meses positivos</div>
            <div class='tend-kpi-val'>{_meses_pos}/12</div>
            <div class='tend-kpi-sub'>Melhor: {_spark_x[_melhor_mes_i]} · Pior: {_spark_x[_pior_mes_i]}</div>
        </div>
    </div>""", unsafe_allow_html=True)

    # ── Gráficos em cards ────────────────────────────────────────────────────
    t1, t2 = st.columns(2, gap="medium")
    with t1:
        _saldo_ano_badge_cls = "green" if _sal_ano_total >= 0 else "red"
        _saldo_ano_badge_txt = ("+" if _sal_ano_total >= 0 else "") + brl(_sal_ano_total)
        st.markdown(f"""<div class='tend-chart-card'>
            <div class='tend-chart-header'>
                <div>
                    <div class='tend-chart-title'>📊 Saldo líquido por mês</div>
                    <div class='tend-chart-sub'>Barras verdes = superávit · vermelhas = déficit</div>
                </div>
                <span class='tend-chart-badge {_saldo_ano_badge_cls}'>{_saldo_ano_badge_txt} no ano</span>
            </div>""", unsafe_allow_html=True)
        _fig_saldo = go.Figure()
        _cores_saldo = ["#30D158" if v >= 0 else "#FF453A" for v in saldo_m]
        _fig_saldo.add_trace(go.Bar(
            x=_spark_x, y=saldo_m, marker_color=_cores_saldo,
            marker_line_width=0, name="Saldo",
            hovertemplate="%{x}: R$ %{y:,.2f}<extra></extra>"
        ))
        _fig_saldo.add_hline(y=0, line_dash="dot", line_color="rgba(161,161,170,.4)", line_width=1)
        _fig_saldo.update_layout(
            margin=dict(l=4,r=4,t=6,b=4),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="rgba(235,235,245,0.6)", size=11), height=260, showlegend=False,
            yaxis=dict(tickprefix="R$ ", gridcolor="rgba(161,161,170,.08)", zeroline=False),
            xaxis=dict(showgrid=False),
            bargap=0.35,
        )
        st.plotly_chart(_fig_saldo, width='stretch', config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    with t2:
        _tend_rec_max  = max(rec_m) if any(rec_m) else 0
        _tend_sai_max  = max(saidas_m) if any(saidas_m) else 0
        st.markdown(f"""<div class='tend-chart-card'>
            <div class='tend-chart-header'>
                <div>
                    <div class='tend-chart-title'>📈 Entradas x saídas</div>
                    <div class='tend-chart-sub'>Comparação mensal ao longo do ano</div>
                </div>
                <span class='tend-chart-badge neutral'>Pico entradas: {brl(_tend_rec_max)}</span>
            </div>""", unsafe_allow_html=True)
        _fig_fluxo = go.Figure()
        _fig_fluxo.add_trace(go.Scatter(
            x=_spark_x, y=rec_m, mode="lines+markers", name="Entradas",
            line=dict(color="#30D158", width=2.5, shape="spline"),
            marker=dict(size=5, color="#30D158"),
            hovertemplate="%{x} Entradas: R$ %{y:,.2f}<extra></extra>"
        ))
        _fig_fluxo.add_trace(go.Scatter(
            x=_spark_x, y=saidas_m, mode="lines+markers", name="Saídas",
            line=dict(color="#FF453A", width=2.5, shape="spline"),
            marker=dict(size=5, color="#FF453A"),
            fill="tozeroy", fillcolor="rgba(255,69,58,0.08)",
            hovertemplate="%{x} Saídas: R$ %{y:,.2f}<extra></extra>"
        ))
        _fig_fluxo.update_layout(
            margin=dict(l=4,r=4,t=6,b=4),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="rgba(235,235,245,0.6)", size=11), height=260,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                        font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
            yaxis=dict(tickprefix="R$ ", gridcolor="rgba(161,161,170,.08)", zeroline=False),
            xaxis=dict(showgrid=False),
        )
        st.plotly_chart(_fig_fluxo, width='stretch', config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)
