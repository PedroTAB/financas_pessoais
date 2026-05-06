"""views/cartao.py - Tela de Cartao."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from utils.color import to_rgba
from utils.charts import spark, bar_mensal, donut, linha_acumulada
from utils.helpers import (
    brl, _parse_brl, _show_feedback,
    MESES_PT, CARTOES, CARTOES_CORES,
)
from config import (
    ANO_MINIMO,
)
from data.storage import (
    get_cartao_compras, add_cartao_compra, update_cartao_compra, delete_cartao_compra,
    get_parcelas_mes, get_projecao_cartao,
    get_cartoes_cfg, add_cartao_cfg, delete_cartao_cfg,
    CATEGORIAS_DEBITO, _cached_records, registrar_historico,
)

now = datetime.now()
ANO_NOW, MES_NOW = now.year, now.month


def show_cartao(username: str):
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

    from datetime import date as _date
    _show_feedback()

    st.markdown("""<div class='cart-page-header'>
            <div>
                <div class='cart-page-title'>💳 Cartão</div>
                <div class='cart-page-sub'>Acompanhe compras parceladas, fatura atual e projeção dos próximos meses</div>
            </div>
    </div>""", unsafe_allow_html=True)

    tab_compras, tab_cartoes = st.tabs(["Compras & Fatura", "Meus Cartões"])

    # ════════════════════════════════════ TAB MEUS CARTÕES ═══════════════════
    with tab_cartoes:
        st.markdown("#### Cartões cadastrados")
        _cfgs = st.session_state.cartoes_cfg
        if _cfgs:
            _cols_c = st.columns(min(len(_cfgs), 3))
            for _i, _cfg in enumerate(_cfgs):
                with _cols_c[_i % 3]:
                    _clr    = _cfg.get("cor", "rgba(235,235,245,0.3)")
                    _nome_c = _cfg.get("nome", "Cartão")
                    _dig_c  = _cfg.get("digitos", "****")
                    _lim_c  = float(_cfg.get("limite", 0))
                    _vec_c  = _cfg.get("vencimento", "")
                    _lim_s  = ("R$ {:,.2f}".format(_lim_c)
                                .replace(",","X").replace(".",",").replace("X","."))
                    html_card = (
                        "<div style='background:linear-gradient(135deg," + _clr + "dd," + _clr + "88);"
                        "border-radius:16px;padding:18px 20px;margin-bottom:8px'>"
                        "<div style='font-size:.72rem;letter-spacing:.14em;color:rgba(255,255,255,.7)'>CARTÃO</div>"
                        "<div style='font-size:1.15rem;font-weight:700;color:#FFFFFF;margin-top:4px'>" + _nome_c + "</div>"
                        "<div style='font-size:.9rem;color:rgba(255,255,255,.8);letter-spacing:.16em;margin-top:10px'>•••• •••• •••• " + str(_dig_c) + "</div>"
                        "<div style='display:flex;justify-content:space-between;margin-top:10px'>"
                        "<div><div style='font-size:.68rem;color:rgba(255,255,255,.6)'>LIMITE</div>"
                        "<div style='font-size:.88rem;font-weight:600;color:#FFFFFF'>" + (_lim_s if _lim_c > 0 else "—") + "</div></div>"
                        "<div><div style='font-size:.68rem;color:rgba(255,255,255,.6)'>VENCIMENTO</div>"
                        "<div style='font-size:.88rem;font-weight:600;color:#FFFFFF'>Dia " + str(_vec_c) + "</div></div>"
                        "</div></div>"
                    )
                    st.markdown(html_card, unsafe_allow_html=True)
                    if st.button("🗑️ Remover " + _nome_c, key="rm_cfg_" + str(_i)):
                        _cfg_id = _cfg.get("id")
                        if _cfg_id:
                            # Excluir todas as compras vinculadas ao cartão antes de removê-lo
                            _df_vinc = get_cartao_compras()
                            if not _df_vinc.empty:
                                _ids_vinc = _df_vinc[_df_vinc["cartao"] == _nome_c]["id"].tolist()
                                for _vid in _ids_vinc:
                                    snap = {"cartao": _nome_c, "descricao": "Compra vinculada", "id": _vid}
                                    registrar_historico(username, "cartao_compra", "delete", int(_vid), snap)
                                    delete_cartao_compra(int(_vid))
                                if _ids_vinc:
                                    _cached_records.clear()
                            # Registrar exclusão do cartão
                            snap_cfg = {"nome": _nome_c, "digitos": _dig_c, "limite": _lim_c, "vencimento": _vec_c}
                            registrar_historico(username, "cartao_config", "delete", int(_cfg_id), snap_cfg)
                            delete_cartao_cfg(int(_cfg_id))
                        st.session_state.pop("cartoes_cfg", None)
                        st.rerun()
        else:
            st.info("Nenhum cartão cadastrado ainda. Adicione abaixo.")

        st.markdown("---")
        st.markdown("#### Adicionar cartão")
        with st.form("form_add_cartao_cfg", clear_on_submit=True):
            _fa1, _fa2 = st.columns(2)
            with _fa1:
                _nome_sel = st.selectbox("Bandeira / Banco", CARTOES, key="cfg_nome")
            with _fa2:
                _dig_inp = st.text_input("4 últimos dígitos", max_chars=4, placeholder="1234", key="cfg_dig")
            _fa3, _fa4 = st.columns(2)
            with _fa3:
                _lim_inp_raw = st.text_input("Limite (R$)", placeholder="Ex: 5.000,00", key="cfg_lim")
                _lim_inp = _parse_brl(_lim_inp_raw) if _lim_inp_raw.strip() else 0.0
            with _fa4:
                _vec_inp = st.number_input("Dia vencimento", min_value=1, max_value=31, value=10, key="cfg_vec")
            _alias_inp = st.text_input("Apelido (opcional)", placeholder="Ex: Nubank Black", key="cfg_alias")
            if st.form_submit_button("➕ Adicionar cartão"):
                _nome_final = _alias_inp.strip() if _alias_inp.strip() else _nome_sel
                _cor_inp = CARTOES_CORES.get(_nome_sel, "#820AD1")
                _ok_cfg, _err_cfg = add_cartao_cfg(
                    _nome_final, _dig_inp.strip() or "****",
                    float(_lim_inp), int(_vec_inp), _cor_inp)
                if _ok_cfg:
                    # Buscar o ID do cartão recém-criado
                    cfg_novo = get_cartoes_cfg(username)
                    novo_cfg = next((c for c in cfg_novo if c["nome"] == _nome_final), None)
                    if novo_cfg:
                        registrar_historico(username, "cartao_config", "create", int(novo_cfg["id"]),
                            {"nome": _nome_final, "digitos": _dig_inp.strip() or "****", "limite": float(_lim_inp), "vencimento": int(_vec_inp)})
                    st.session_state.pop("cartoes_cfg", None)
                    st.rerun()
                else:
                    st.error("Erro ao salvar cartão: " + str(_err_cfg))

    # ════════════════════════════════ TAB COMPRAS & FATURA ═══════════════════
    with tab_compras:

        st.markdown("""<style>
        .cart-page-header{display:flex;align-items:flex-start;justify-content:space-between;
            margin-bottom:20px;padding-bottom:16px;border-bottom:1px solid rgba(161,161,170,.1)}
        .cart-page-title{font-size:1.5rem;font-weight:800;color:#FFFFFF;letter-spacing:-.02em;line-height:1.1}
        .cart-page-sub{font-size:.82rem;color:rgba(235,235,245,0.3);margin-top:4px}
        .cart-form-badge{display:inline-flex;align-items:center;gap:6px;font-size:.7rem;
            font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:3px 10px;
            border-radius:999px;background:rgba(10,132,255,0.15);color:#0A84FF;margin-bottom:12px}
        .cart-list-header{display:flex;justify-content:space-between;align-items:center;margin:18px 0 10px}
        .cart-list-title{font-size:.82rem;font-weight:700;color:rgba(235,235,245,0.6);letter-spacing:.06em;text-transform:uppercase}
        .cart-list-total{font-size:1rem;font-weight:800;color:#0A84FF}
        .cart-empty{text-align:center;padding:32px 0;color:rgba(235,235,245,0.3);font-size:.88rem}
        .cart-proj-title{font-size:.82rem;font-weight:700;color:rgba(235,235,245,0.6);letter-spacing:.06em;text-transform:uppercase;margin:18px 0 10px}
        </style>""", unsafe_allow_html=True)

        # ── helper limpar form ────────────────────────────────────────────────
        def _clear_cart_form():
            for _k in ["c_cartao","c_cat","c_desc","c_vt","c_np","c_mi","c_ai"]:
                st.session_state.pop(_k, None)
            st.session_state.edit_cartao = None

        # ── recarregar dados frescos ──────────────────────────────────────────
        _df_live = get_cartao_compras()
        _nomes_reg = [c["nome"] for c in st.session_state.cartoes_cfg]

        if not _nomes_reg:
            st.warning("⚠️ Nenhum cartão cadastrado. Vá em **Meus Cartões** para adicionar um antes de registrar compras.")

        # ── filtros ───────────────────────────────────────────────────────────
        _fc1, _fc2, _fc3 = st.columns(3)
        with _fc1:
            _opts_f = ["Todos"] + _nomes_reg if _nomes_reg else ["Todos"]
            f_cartao = st.selectbox("Cartão", _opts_f, key="cart_f_cartao")
        with _fc2:
            _anos_c = sorted(set([ANO_NOW] + (
                _df_live["ano_inicio"].unique().tolist() if not _df_live.empty else []
            )), reverse=True)
            ano_c = st.selectbox("Ano", _anos_c, key="cart_f_ano")
        with _fc3:
            mes_c = st.selectbox("Mês", list(range(1,13)),
                format_func=lambda x: MESES_PT[x], index=MES_NOW-1, key="cart_f_mes")

        df_cf = _df_live.copy()
        if f_cartao != "Todos" and not df_cf.empty:
            df_cf = df_cf[df_cf["cartao"] == f_cartao]

        parc_mes     = get_parcelas_mes(df_cf, ano_c, mes_c)
        total_fatura = parc_mes["valor_parcela"].sum() if not parc_mes.empty else 0.0
        _hoje        = _date.today()
        _abertas = 0
        if not df_cf.empty:
            for _, _r in df_cf.iterrows():
                _ult = int(_r["ano_inicio"])*12 + int(_r["mes_inicio"])-1 + int(_r["num_parcelas"])-1
                if _ult >= _hoje.year*12 + _hoje.month - 1:
                    _abertas += 1
        if f_cartao == "Todos":
            _limite_kpi = sum(float(c["limite"]) for c in st.session_state.cartoes_cfg if str(c.get("limite","0")).strip())
        else:
            _cfg_sel    = next((c for c in st.session_state.cartoes_cfg if c["nome"] == f_cartao), None)
            _limite_kpi = float(_cfg_sel["limite"]) if _cfg_sel else 0.0
        _lim_pct    = (total_fatura / _limite_kpi * 100) if _limite_kpi > 0 else 0.0
        _proj6      = get_projecao_cartao(df_cf, meses=6)
        total_6m    = _proj6["total"].sum() if not _proj6.empty else 0.0

        # ── KPIs (mantidos) ───────────────────────────────────────────────────
        _kc1,_kc2,_kc3,_kc4 = st.columns(4)
        with _kc1:
            st.markdown("<div class='kpi cartao'><div class='kpi-lbl'>FATURA DO MÊS</div><div class='kpi-val'>"
                + brl(total_fatura) + "</div><div class='kpi-sub'>"
                + str(len(parc_mes)) + " parcela(s) em "
                + MESES_PT[mes_c][:3] + "/" + str(ano_c)[2:] + "</div></div>", unsafe_allow_html=True)
        with _kc2:
            st.markdown("<div class='kpi cartao'><div class='kpi-lbl'>LIMITE UTILIZADO</div><div class='kpi-val'>"
                + "{:.1f}%".format(_lim_pct) + "</div><div class='kpi-sub'>"
                + ("de " + brl(_limite_kpi) if _limite_kpi else "Configure em Meus Cartões")
                + "</div></div>", unsafe_allow_html=True)
        with _kc3:
            st.markdown("<div class='kpi cartao'><div class='kpi-lbl'>COMPRAS EM ABERTO</div><div class='kpi-val'>"
                + str(_abertas) + "</div><div class='kpi-sub'>com parcelas futuras</div></div>", unsafe_allow_html=True)
        with _kc4:
            st.markdown("<div class='kpi cartao'><div class='kpi-lbl'>COMPROMETIDO 6M</div><div class='kpi-val'>"
                + brl(total_6m) + "</div><div class='kpi-sub'>próximos 6 meses</div></div>", unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        # ── estado de edição ──────────────────────────────────────────────────
        eid_c = st.session_state.edit_cartao
        row_c = None
        if eid_c and not _df_live.empty:
            _mc = _df_live[_df_live["id"] == eid_c]
            if not _mc.empty:
                row_c = _mc.iloc[0]
        if eid_c and row_c is not None:
            st.info("✏️ Editando #" + str(eid_c) + " — " + str(row_c["descricao"]) + " · Clique em **Cancelar edição** para descartar")

        # ── pré-popular campos ────────────────────────────────────────────────
        if not _nomes_reg:
            st.stop()
        if "c_cartao" not in st.session_state:
            st.session_state["c_cartao"] = str(row_c["cartao"]) if row_c is not None else (_nomes_reg[0] if _nomes_reg else CARTOES[0])
        if "c_cat" not in st.session_state:
            st.session_state["c_cat"] = str(row_c["categoria"]) if row_c is not None else CATEGORIAS_DEBITO[0]
        if "c_desc" not in st.session_state:
            st.session_state["c_desc"] = str(row_c["descricao"]) if row_c is not None else ""
        if "c_vt" not in st.session_state:
            st.session_state["c_vt"] = (brl(float(row_c["valor_total"])).replace("R$ ","") if row_c is not None else "")
        if "c_np" not in st.session_state:
            st.session_state["c_np"] = int(row_c["num_parcelas"]) if row_c is not None else 1
        if "c_mi" not in st.session_state:
            st.session_state["c_mi"] = int(row_c["mes_inicio"]) if row_c is not None else MES_NOW
        if "c_ai" not in st.session_state:
            st.session_state["c_ai"] = int(row_c["ano_inicio"]) if row_c is not None else ANO_NOW

        _cart_opts = _nomes_reg if _nomes_reg else CARTOES
        if st.session_state["c_cartao"] not in _cart_opts:
            st.session_state["c_cartao"] = _cart_opts[0]
        if st.session_state["c_cat"] not in CATEGORIAS_DEBITO:
            st.session_state["c_cat"] = CATEGORIAS_DEBITO[0]

        # ── formulário reimaginado ────────────────────────────────────────────
        with st.container(border=True):
            _badge_cart = st.session_state.get("c_cartao", _cart_opts[0] if _cart_opts else "Cartão")
            st.markdown(f"<div class='cart-form-badge'>💳 {_badge_cart}</div>", unsafe_allow_html=True)

            _cf1, _cf2 = st.columns(2)
            with _cf1:
                cart_inp = st.selectbox("Cartão", _cart_opts, key="c_cartao")
            with _cf2:
                cat_inp_c = st.selectbox("Categoria", CATEGORIAS_DEBITO, key="c_cat")

            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

            _cf3, _cf4 = st.columns([2,1])
            with _cf3:
                desc_c = st.text_input("Descrição", key="c_desc", placeholder="Ex: Supermercado, Passagem, Curso...")
            with _cf4:
                vt_raw_c = st.text_input("Valor Total (R$)", placeholder="Ex: 1.200,00", key="c_vt")
                vt_c = _parse_brl(vt_raw_c)

            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

            _cf5, _cf6, _cf7 = st.columns([1,1,1])
            with _cf5:
                np_c = st.number_input("Nº Parcelas", min_value=1, max_value=60, step=1, key="c_np")
            with _cf6:
                mi_c = st.selectbox("Mês Início", list(range(1,13)),
                    format_func=lambda x: MESES_PT[x], key="c_mi")
            with _cf7:
                ai_c = st.number_input("Ano Início", min_value=2020, max_value=ANO_NOW+5,
                    step=1, key="c_ai")

            if np_c > 0 and vt_c > 0:
                _ultima_m = ((mi_c-1+np_c-1)%12)+1
                _ultima_a = ai_c + (mi_c-1+np_c-1)//12
                st.markdown(
                    f"<div style='font-size:.78rem;color:rgba(235,235,245,0.6);margin-top:6px'>"
                    f"Parcela: <b style='color:#FFFFFF'>{brl(round(vt_c/np_c,2))}</b> × {int(np_c)}x"
                    f" <span style='color:rgba(235,235,245,0.3)'>·</span> Última: <b style='color:#0A84FF'>{MESES_PT[_ultima_m]}/{_ultima_a}</b>"
                    f"</div>", unsafe_allow_html=True)

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            _bc1, _bc2 = st.columns(2)
            with _bc1:
                _lbl_btn = "💾 Salvar compra" if not eid_c else "💾 Atualizar compra"
                _salvar_c = st.button(_lbl_btn, key="cart_salvar", width='stretch')
            with _bc2:
                _lbl_canc_cart = "✕ Cancelar edição" if eid_c else "↺ Limpar campos"
                _limpar_c = st.button(_lbl_canc_cart, key="cart_limpar",
                    width='stretch', on_click=_clear_cart_form)

        if _limpar_c:
            st.rerun()

        if _salvar_c:
            if not desc_c.strip():
                st.error("Informe a descrição!")
            elif vt_c <= 0:
                st.error("Informe um valor válido!")
            else:
                if eid_c:
                    ok, err = update_cartao_compra(eid_c, cart_inp, desc_c.strip(),
                        cat_inp_c, vt_c, int(np_c), int(ai_c), mi_c)
                    if ok:
                        registrar_historico(username, "cartao_compra", "update", eid_c,
                            {"cartao": cart_inp, "descricao": desc_c.strip(), "categoria": cat_inp_c, "valor_total": vt_c, "num_parcelas": int(np_c)})
                else:
                    ok, err = add_cartao_compra(cart_inp, desc_c.strip(),
                        cat_inp_c, vt_c, int(np_c), int(ai_c), mi_c)
                    if ok:
                        # Buscar o ID do registro recém-criado
                        df_novo = get_cartao_compras(username)
                        novo = df_novo[(df_novo["cartao"] == cart_inp) & (df_novo["descricao"] == desc_c.strip())]
                        if not novo.empty:
                            novo_id = int(novo.iloc[0]["id"])
                            registrar_historico(username, "cartao_compra", "create", novo_id,
                                {"cartao": cart_inp, "descricao": desc_c.strip(), "categoria": cat_inp_c, "valor_total": vt_c, "num_parcelas": int(np_c)})
                if ok:
                    _cached_records.clear()
                    _clear_cart_form()
                    st.session_state["_msg_ok"] = (
                        "✅ Compra atualizada!" if eid_c else "✅ Compra registrada!")
                    st.rerun()
                else:
                    st.error(err or "Erro ao salvar compra.")

        # ── lista de parcelas do mês ──────────────────────────────────────────
        st.divider()
        st.markdown(f"""<div class='cart-list-header'>
            <div class='cart-list-title'>Parcelas de {MESES_PT[mes_c]}/{ano_c}</div>
            <div class='cart-list-total'>{brl(total_fatura)} total</div>
        </div>""", unsafe_allow_html=True)

        if not parc_mes.empty:
            _hc1,_hc2,_hc3,_hc4,_hc5,_hc6 = st.columns([2.8,1.2,1.2,0.9,1.3,0.7])
            for _lbl, _col in zip(["DESCRIÇÃO / CARTÃO","PARCELA","TOTAL","Nº","CATEGORIA",""],
                                  [_hc1,_hc2,_hc3,_hc4,_hc5,_hc6]):
                _col.markdown("<span style='font-size:.72rem;color:rgba(235,235,245,0.3);text-transform:uppercase;letter-spacing:.06em'>"
                    + _lbl + "</span>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:.2rem 0 .4rem;opacity:.1'>", unsafe_allow_html=True)

            for _, _pr in parc_mes.sort_values(["cartao","categoria","descricao"]).iterrows():
                _pc1,_pc2,_pc3,_pc4,_pc5,_pc6 = st.columns([2.8,1.2,1.2,0.9,1.3,0.7])
                _pc1.markdown("**" + str(_pr["descricao"]) + "**  \n"
                    + "<span style='font-size:.8rem;color:rgba(235,235,245,0.3)'>" + str(_pr["cartao"]) + "</span>",
                    unsafe_allow_html=True)
                _pc2.markdown(brl(_pr["valor_parcela"]))
                _pc3.markdown("<span style='color:rgba(235,235,245,0.6);font-size:.85rem'>" + brl(float(_pr.get("valor_total", _pr["valor_parcela"] * int(_pr["total_parcelas"])))) + "</span>", unsafe_allow_html=True)
                _pc4.markdown(str(int(_pr["parcela_atual"])) + "/" + str(int(_pr["total_parcelas"])))
                _pc5.markdown(str(_pr["categoria"]))
                with _pc6:
                    _id_pr = int(_pr["id_compra"])
                    if st.button("✏️", key="ec_" + str(_id_pr), help="Editar"):
                        _clear_cart_form()
                        st.session_state.edit_cartao = _id_pr
                        st.rerun()
                    if st.button("🗑️", key="dc_" + str(_id_pr), help="Excluir"):
                        # Registrar histórico antes de excluir
                        snap = {"cartao": _pr["cartao"], "descricao": _pr["descricao"], "categoria": _pr["categoria"], "valor_parcela": float(_pr["valor_parcela"]), "parcela_atual": int(_pr["parcela_atual"]), "total_parcelas": int(_pr["total_parcelas"])}
                        registrar_historico(username, "cartao_compra", "delete", _id_pr, snap)
                        ok_d, err_d = delete_cartao_compra(_id_pr)
                        _cached_records.clear()
                        st.session_state["_msg_ok" if ok_d else "_msg_err"] = (
                            "🗑️ Compra excluída!" if ok_d else "❌ " + (err_d or "Erro ao excluir."))
                        st.rerun()
                st.markdown("<div style='height:1px;background:rgba(255,255,255,.05);margin:.1rem 0'></div>",
                    unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='cart-empty'>Nenhuma parcela em {MESES_PT[mes_c]}/{ano_c}.<br><span style='font-size:.78rem'>Registre uma compra acima para começar.</span></div>", unsafe_allow_html=True)

        # ── projeção 6 meses ──────────────────────────────────────────────────
        st.divider()
        st.markdown("<div class='cart-proj-title'>Projeção próximos 6 meses</div>", unsafe_allow_html=True)

        _meses_seq, _labels_6m = [], []
        _a, _m = _hoje.year, _hoje.month
        for _ in range(6):
            _meses_seq.append((_a, _m))
            _labels_6m.append(MESES_PT[_m][:3] + "/" + str(_a)[2:])
            _m += 1
            if _m > 12: _m = 1; _a += 1

        _proj_data = {}
        for _nc in (_nomes_reg if _nomes_reg else []):
            if f_cartao != "Todos" and _nc != f_cartao:
                continue
            _df_nc = _df_live[_df_live["cartao"] == _nc].copy() if not _df_live.empty else _df_live.copy()
            _vals = [get_parcelas_mes(_df_nc, _pa, _pm)["valor_parcela"].sum()
                     if not get_parcelas_mes(_df_nc, _pa, _pm).empty else 0.0
                     for (_pa, _pm) in _meses_seq]
            _proj_data[_nc] = _vals

        if _proj_data and any(sum(v) > 0 for v in _proj_data.values()):
            _fig = go.Figure()
            for _nc, _vals in _proj_data.items():
                _cfg_c = next((c for c in st.session_state.cartoes_cfg if c["nome"] == _nc), None)
                _cor_c = _cfg_c["cor"] if _cfg_c else "#0A84FF"
                _fig.add_trace(go.Bar(
                    name=_nc, x=_labels_6m, y=_vals,
                    marker_color=_cor_c,
                    text=[brl(v) if v > 0 else "" for v in _vals],
                    textposition="outside",
                    textfont=dict(color=_cor_c, size=10),
                ))
            _fig.update_layout(
                barmode="stack",
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=20, b=0, l=0, r=0), height=280,
                legend=dict(orientation="h", y=-0.2, font=dict(color="rgba(235,235,245,0.6)", size=11)),
                xaxis=dict(gridcolor="rgba(255,255,255,0.04)", color="rgba(235,235,245,0.3)", tickfont=dict(size=11)),
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)", color="rgba(235,235,245,0.3)",
                           zeroline=False, tickformat=",.0f"),
                font=dict(color="rgba(235,235,245,0.6)"),
            )
            st.plotly_chart(_fig, width='stretch', config={"displayModeBar": False})
        else:
            st.markdown("<div class='cart-empty' style='padding-top:16px'>Sem dados para projeção.</div>", unsafe_allow_html=True)
