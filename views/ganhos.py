"""views/ganhos.py - Ganhos."""
import streamlit as st
import pandas as pd
from datetime import datetime

from utils.helpers import (
    brl, _parse_brl, _show_feedback,
    MESES_PT, MESES_ABR
)
from data.storage import (
    get_lancamentos, add_lancamento, update_lancamento, delete_lancamento,
    get_ganhos, add_ganho, update_ganho, delete_ganho,
    calc_inss, calc_irrf,
    TIPOS_GANHO, TIPOS_INV, INSS_FAIXAS, INSS_TETO, IRRF_FAIXAS, IRRF_DED_DEP,
    registrar_historico,
)

now = datetime.now()
ANO_NOW, MES_NOW = now.year, now.month


def show_ganhos(username: str):
    df_all = get_lancamentos(username)
    df_ganho = get_ganhos(username)
    ANO = st.session_state.get("ano_sel", ANO_NOW)
    MES = st.session_state.get("mes_sel", MES_NOW)

    _show_feedback()

    st.markdown(
        """
        <style>
        .ganhos-page-header{display:flex;align-items:flex-start;justify-content:space-between;
            margin-bottom:20px;padding-bottom:16px;border-bottom:1px solid rgba(161,161,170,.1)}
        .ganhos-page-title{font-size:1.5rem;font-weight:800;color:#FFFFFF;letter-spacing:-.02em;line-height:1.1}
        .ganhos-page-sub{font-size:.82rem;color:rgba(235,235,245,0.3);margin-top:4px}
        .ganhos-form-card{background:#1C1C1E;border:0.5px solid rgba(255,255,255,0.08);
            border-radius:16px;padding:20px 22px;margin-bottom:16px}
        .ganhos-form-section{font-size:.7rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;
            color:rgba(235,235,245,0.3);margin-bottom:14px;padding-bottom:8px;border-bottom:1px solid rgba(84,84,88,0.36)}
        .ganhos-list-header{display:flex;justify-content:space-between;align-items:center;
            margin:20px 0 12px}
        .ganhos-list-title{font-size:.82rem;font-weight:700;color:rgba(235,235,245,0.6);letter-spacing:.06em;
            text-transform:uppercase}
        .ganhos-list-total{font-size:1rem;font-weight:800;color:#30D158}
        .ganhos-row{display:grid;grid-template-columns:36px 120px 1fr 130px 80px;
            align-items:center;gap:12px;padding:10px 0;
            border-bottom:1px solid rgba(255,255,255,0.06)}
        .ganhos-row:last-child{border-bottom:none}
        .ganhos-row-dot{width:10px;height:10px;border-radius:50%;background:#30D158;flex-shrink:0}
        .ganhos-row-tipo{font-size:.85rem;font-weight:700;color:#FFFFFF}
        .ganhos-row-det{font-size:.8rem;color:rgba(235,235,245,0.3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
        .ganhos-row-val{font-size:.92rem;font-weight:700;color:#30D158;text-align:right;font-variant-numeric:tabular-nums}
        .ganhos-empty{text-align:center;padding:32px 0;color:rgba(235,235,245,0.3);font-size:.88rem}
        .ganho-tipo-badge{display:inline-flex;align-items:center;gap:5px;font-size:.7rem;
            font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:3px 10px;
            border-radius:999px;background:rgba(48,209,88,0.15);color:#30D158;margin-bottom:12px}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class='ganhos-page-header'>
            <div>
                <div class='ganhos-page-title'>💰 Ganhos</div>
                <div class='ganhos-page-sub'>Registre salários, investimentos, aluguéis e outras receitas</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    grow, grow_ex = None, {}
    eid = st.session_state.get("edit_ganho")
    if eid:
        m = df_ganho[df_ganho["id"] == eid]
        if not m.empty:
            grow = m.iloc[0]
            grow_ex = grow["extras"] if isinstance(grow["extras"], dict) else {}
            st.info(f"✏️ Editando #{eid} — {grow['tipo_ganho']} · Clique em **Cancelar edição** para descartar")

    tipo_icons = {"Salário": "💼", "Investimento": "📈", "Aluguel": "🏠", "Freelance": "💻", "Outros": "📦"}

    with st.container(border=True):
        col_ano, col_mes, col_tipo = st.columns(3)
        anos_g = list(range(2025, ANO_NOW + 1))

        with col_ano:
            ano_g = st.selectbox(
                "Ano",
                anos_g,
                index=anos_g.index(int(grow["ano"])) if grow is not None else anos_g.index(ANO),
                format_func=str,
                key="g_ano",
            )

        meses_g = list(MESES_PT.keys())
        mes_g_def = int(grow["mes"]) if grow is not None else MES
        with col_mes:
            mes_g = st.selectbox(
                "Mês",
                meses_g,
                index=meses_g.index(mes_g_def),
                format_func=lambda x: MESES_PT[x],
                key="g_mes",
            )

        with col_tipo:
            tipo_g = st.selectbox(
                "Tipo de Ganho",
                TIPOS_GANHO,
                index=TIPOS_GANHO.index(grow["tipo_ganho"]) if grow is not None else 0,
                key="g_tipo",
            )

        st.markdown(
            f"<div class='ganho-tipo-badge'>{tipo_icons.get(tipo_g, '💰')} {tipo_g}</div>",
            unsafe_allow_html=True,
        )

        if tipo_g == "Salário":
            cL, cR = st.columns([1.1, 1])

            with cL:
                st.markdown("##### 📝 Dados do Salário")

                if "sal_form_init" not in st.session_state:
                    st.session_state.sal_form_init = True
                    st.session_state["s_bruto"] = ""
                    st.session_state["s_deps"] = 0
                    st.session_state["s_odesc"] = ""
                    st.session_state["s_oval"] = ""
                    if grow_ex:
                        if grow_ex.get("bruto"):
                            try:
                                st.session_state["s_bruto"] = f"{float(grow_ex['bruto']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                            except Exception:
                                st.session_state["s_bruto"] = ""
                        st.session_state["s_deps"] = int(grow_ex.get("deps", 0)) if grow_ex else 0
                        st.session_state["s_odesc"] = str(grow_ex.get("o_desc", "")) if grow_ex else ""
                        if grow_ex.get("o_val"):
                            try:
                                st.session_state["s_oval"] = f"{float(grow_ex['o_val']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                            except Exception:
                                st.session_state["s_oval"] = ""

                bruto_raw = st.text_input("Salário Bruto (R$)", placeholder="Ex: 7.000,00", key="s_bruto")
                deps = st.number_input("Dependentes (IRRF)", min_value=0, max_value=20, step=1, key="s_deps")

                c1d, c2d = st.columns(2)
                with c1d:
                    o_desc = st.text_input("Desc. outros descontos", placeholder="Ex: VT, VR…", key="s_odesc")
                with c2d:
                    oval_raw = st.text_input("Valor outros descontos (R$)", placeholder="Ex: 300,00", key="s_oval")

            bruto = _parse_brl(bruto_raw)
            o_val = _parse_brl(oval_raw)
            inss = calc_inss(bruto) if bruto > 0 else 0.0
            irrf = calc_irrf(bruto, inss, int(deps)) if bruto > 0 else 0.0
            liq = round(bruto - inss - irrf - o_val, 2)

            with cR:
                st.markdown("##### 📊 Resultado")
                cor_liq = "#30D158" if liq >= 0 else "#FF453A"

                def _card_row(icon, label, valor, color, bold=False, size="0.9rem"):
                    b = "700" if bold else "400"
                    return (
                        f"<tr><td style='color:{color};padding:6px 0;font-weight:{b};font-size:{size}'>"
                        f"{icon} {label}</td>"
                        f"<td style='text-align:right;color:{color};font-weight:{b};font-size:{size}'>"
                        f"{valor}</td></tr>"
                    )

                rows = (
                    _card_row("💼", "Salário Bruto", brl(bruto), "#ffffff", bold=True)
                    + _card_row("🔻", "INSS", f"- {brl(inss)}", "#FF6B63")
                    + _card_row("🔻", "IRRF", f"- {brl(irrf)}", "#FF6B63")
                    + _card_row("🔻", o_desc or "Outros", f"- {brl(o_val)}", "#FF6B63")
                )

                st.markdown(
                    f"""
                    <div style='background:linear-gradient(135deg,#1C1C1E,#1C1C1E);
                         border:1px solid #2C2C2E;border-radius:16px;padding:1.2rem 1.4rem;'>
                      <table style='width:100%;border-collapse:collapse;'>{rows}</table>
                      <div style='border-top:1px solid #2C2C2E;margin-top:8px;padding-top:10px;
                           display:flex;justify-content:space-between;align-items:center;'>
                        <span style='color:{cor_liq};font-weight:700;font-size:1rem'>💚 Salário Líquido</span>
                        <span style='color:{cor_liq};font-weight:800;font-size:1.4rem'>{brl(liq)}</span>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.markdown("<br>", unsafe_allow_html=True)

                with st.expander("ℹ️ Tabelas INSS / IRRF 2025"):
                    t1, t2 = st.columns(2)
                    with t1:
                        st.markdown("**INSS Progressivo**")
                        rows_t = "".join(
                            f"<tr><td>Até {brl(l)}</td><td>{a*100:.1f}%</td></tr>"
                            for l, a in INSS_FAIXAS
                        )
                        rows_t += f"<tr><td><b>Teto</b></td><td><b>{brl(INSS_TETO)}</b></td></tr>"
                        st.markdown(
                            f"<table style='font-size:.78rem;width:100%'>"
                            f"<tr><th>Faixa</th><th>Alíq.</th></tr>{rows_t}</table>",
                            unsafe_allow_html=True,
                        )
                    with t2:
                        st.markdown("**IRRF após INSS**")
                        rows_t = "".join(
                            f"<tr><td>{'Acima' if l == float('inf') else 'Até ' + brl(l)}</td>"
                            f"<td>{a*100:.1f}%</td><td>{brl(d)}</td></tr>"
                            for l, a, d in IRRF_FAIXAS
                        )
                        rows_t += f"<tr><td colspan='3'>Dep.: {brl(IRRF_DED_DEP)}/dep.</td></tr>"
                        st.markdown(
                            f"<table style='font-size:.78rem;width:100%'>"
                            f"<tr><th>Base</th><th>Alíq.</th><th>Ded.</th></tr>{rows_t}</table>",
                            unsafe_allow_html=True,
                        )

            st.markdown("<br>", unsafe_allow_html=True)
            replicar_12 = st.checkbox(
                "📅 Replicar este salário para todos os meses do ano",
                value=False,
                key="sal_replicar",
                help="Salva o mesmo salário nos 12 meses a partir do mês selecionado. Sobrescreve meses que já têm salário cadastrado.",
            )
            ba, bb = st.columns([1, 1])
            with ba:
                salvar_sal = st.button("💾 Salvar Salário", width='stretch', key="sal_save")
            with bb:
                lbl_canc_sal = "❌ Cancelar edição" if st.session_state.get("edit_ganho") else "🧹 Limpar campos"
                limpar_sal = st.button(lbl_canc_sal, width='stretch', key="sal_cancel")

            if salvar_sal:
                if bruto <= 0:
                    st.error("Informe o salário bruto!")
                else:
                    extras_sal = {
                        "bruto": bruto,
                        "inss": inss,
                        "irrf": irrf,
                        "deps": int(deps),
                        "o_desc": o_desc,
                        "o_val": o_val,
                    }

                    if replicar_12:
                        atualizados, inseridos = [], []
                        cur_m, cur_a = mes_g, ano_g
                        for _ in range(12):
                            existe_id = None
                            if not df_ganho.empty:
                                mask = (
                                    (df_ganho["ano"] == cur_a)
                                    & (df_ganho["mes"] == cur_m)
                                    & (df_ganho["tipo_ganho"] == "Salário")
                                )
                                if mask.any():
                                    existe_id = int(df_ganho.loc[mask, "id"].iloc[0])

                            if existe_id is not None:
                                update_ganho(username, existe_id, cur_a, cur_m, "Salário", "Salário", liq, extras_sal)
                                registrar_historico(username, "ganho", "update", existe_id, {"tipo_ganho": "Salário", "valor_liquido": liq, "ano": cur_a, "mes": cur_m})
                                atualizados.append(f"{MESES_PT[cur_m]}/{cur_a}")
                            else:
                                ok, _ = add_ganho(username, cur_a, cur_m, "Salário", "Salário", liq, extras_sal)
                                if ok:
                                    # Buscar o ID do registro recém-criado
                                    df_novo = get_ganhos(username)
                                    novo = df_novo[(df_novo["ano"] == cur_a) & (df_novo["mes"] == cur_m) & (df_novo["tipo_ganho"] == "Salário")]
                                    if not novo.empty:
                                        novo_id = int(novo.iloc[0]["id"])
                                        registrar_historico(username, "ganho", "create", novo_id, {"tipo_ganho": "Salário", "valor_liquido": liq, "ano": cur_a, "mes": cur_m})
                                inseridos.append(f"{MESES_PT[cur_m]}/{cur_a}")

                            cur_m += 1
                            if cur_m > 12:
                                cur_m = 1
                                cur_a += 1

                        st.session_state.edit_ganho = None
                        total = len(atualizados) + len(inseridos)
                        msg = f"✅ Salário replicado em **{total} meses**"
                        if inseridos:
                            msg += f"\n\n➕ Novos: {', '.join(inseridos)}"
                        if atualizados:
                            msg += f"\n\n🔄 Atualizados: {', '.join(atualizados)}"
                        st.session_state["msg_ok"] = msg
                    elif eid and grow is not None:
                        ok_u, err_u = update_ganho(username, eid, ano_g, mes_g, "Salário", "Salário", liq, extras_sal)
                        if ok_u:
                            registrar_historico(username, "ganho", "update", eid, {"tipo_ganho": "Salário", "valor_liquido": liq, "ano": ano_g, "mes": mes_g})
                            st.session_state.edit_ganho = None
                            st.session_state["msg_ok"] = f"✅ Salário atualizado! Líquido: {brl(liq)}"
                        else:
                            st.error(err_u or "Erro ao atualizar salário. Tente novamente.")
                    else:
                        ok, err_sal = add_ganho(username, ano_g, mes_g, "Salário", "Salário", liq, extras_sal)
                        if ok:
                            df_novo = get_ganhos(username)
                            novo = df_novo[(df_novo["ano"] == ano_g) & (df_novo["mes"] == mes_g) & (df_novo["tipo_ganho"] == "Salário")]
                            if not novo.empty:
                                novo_id = int(novo.iloc[0]["id"])
                                registrar_historico(username, "ganho", "create", novo_id, {"tipo_ganho": "Salário", "valor_liquido": liq, "ano": ano_g, "mes": mes_g})
                            st.session_state["msg_ok"] = f"✅ Salário salvo! Líquido: {brl(liq)}"
                        else:
                            st.error(err_sal or "Erro ao salvar salário. Tente novamente.")

                    st.session_state.pop("sal_form_init", None)
                    st.rerun()

            if limpar_sal:
                for k in ["s_bruto", "s_deps", "s_odesc", "s_oval", "sal_replicar"]:
                    st.session_state.pop(k, None)
                st.session_state.edit_ganho = None
                st.session_state.pop("sal_form_init", None)
                st.rerun()

        else:
            valor_final, extras_final = 0.0, {}

            if tipo_g == "Investimento":
                ia, ib = st.columns(2)
                with ia:
                    tipo_inv = st.selectbox(
                        "Tipo de investimento",
                        TIPOS_INV,
                        index=TIPOS_INV.index(grow_ex.get("tipo_inv", "Renda Fixa")) if grow_ex else 0,
                    )
                    onde = st.text_input("Onde (banco/corretora)", value=grow_ex.get("onde", ""))
                with ib:
                    v_inv_def = (
                        f"{float(grow_ex['v_inv']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        if grow_ex.get("v_inv") else ""
                    )
                    v_inv_raw = st.text_input("Valor investido", value=v_inv_def, placeholder="Ex: 1.500,00", key="vinv")
                    v_inv = _parse_brl(v_inv_raw)
                    rend_def = (
                        f"{float(grow_ex['rend']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        if grow_ex.get("rend") else ""
                    )
                    rend_raw = st.text_input("Rendimento recebido", value=rend_def, placeholder="Ex: 150,00", key="rend")
                    rend = _parse_brl(rend_raw)
                valor_final = rend
                extras_final = {"tipo_inv": tipo_inv, "onde": onde, "v_inv": v_inv, "rend": rend}

            elif tipo_g == "Aluguel":
                ia2, ib2 = st.columns(2)
                with ia2:
                    imovel = st.text_input("Imóvel / endereço", value=grow_ex.get("imovel", ""))
                with ib2:
                    val_def2 = (
                        f"{float(grow['valor_liquido']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        if grow is not None else ""
                    )
                    val_raw2 = st.text_input("Valor recebido", value=val_def2, placeholder="Ex: 2.000,00", key="val_alug")
                    valor_final = _parse_brl(val_raw2)
                extras_final = {"imovel": imovel}

            elif tipo_g == "Freelance":
                ia3, ib3 = st.columns(2)
                with ia3:
                    cliente = st.text_input("Cliente / projeto", value=grow_ex.get("cliente", ""))
                with ib3:
                    val_def3 = (
                        f"{float(grow['valor_liquido']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        if grow is not None else ""
                    )
                    val_raw3 = st.text_input("Valor recebido", value=val_def3, placeholder="Ex: 3.500,00", key="val_free")
                    valor_final = _parse_brl(val_raw3)
                extras_final = {"cliente": cliente}

            else:
                oa, ob = st.columns(2)
                with oa:
                    obs = st.text_area("Observação", value=grow_ex.get("obs", ""), height=70)
                with ob:
                    val_def4 = (
                        f"{float(grow['valor_liquido']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        if grow is not None else ""
                    )
                    val_raw4 = st.text_input("Valor recebido", value=val_def4, placeholder="Ex: 500,00", key="val_out")
                    valor_final = _parse_brl(val_raw4)
                extras_final = {"obs": obs}

            sb_g, can_g = st.columns(2)
            with sb_g:
                ok_g = st.button("💾 Salvar", width='stretch', key="ganho_salvar")
            lbl_canc_ganho = "✕ Cancelar edição" if st.session_state.get("edit_ganho") else "↺ Limpar campos"
            with can_g:
                can_gx = st.button(lbl_canc_ganho, width='stretch', key="ganho_cancelar")

            if ok_g:
                if valor_final <= 0:
                    st.error("Valor deve ser maior que zero!")
                else:
                    if eid and grow is not None:
                        ok_u, err_u = update_ganho(username, eid, ano_g, mes_g, tipo_g, tipo_g, valor_final, extras_final)
                        if ok_u:
                            registrar_historico(username, "ganho", "update", eid, {"tipo_ganho": tipo_g, "valor_liquido": valor_final, "ano": ano_g, "mes": mes_g})
                            st.session_state.edit_ganho = None
                            st.session_state["msg_ok"] = "✅ Ganho atualizado com sucesso!"
                            st.rerun()
                        else:
                            st.error(err_u or "Erro ao atualizar ganho. Tente novamente.")
                    else:
                        ok, err_g = add_ganho(username, ano_g, mes_g, tipo_g, tipo_g, valor_final, extras_final)
                        if ok:
                            df_novo = get_ganhos(username)
                            novo = df_novo[(df_novo["ano"] == ano_g) & (df_novo["mes"] == mes_g) & (df_novo["tipo_ganho"] == tipo_g)]
                            if not novo.empty:
                                novo_id = int(novo.iloc[0]["id"])
                                registrar_historico(username, "ganho", "create", novo_id, {"tipo_ganho": tipo_g, "valor_liquido": valor_final, "ano": ano_g, "mes": mes_g})
                            st.session_state["msg_ok"] = "✅ Ganho salvo com sucesso!"
                            st.rerun()
                        else:
                            st.error(err_g or "Erro ao salvar ganho. Tente novamente.")

            if can_gx:
                st.session_state.edit_ganho = None
                st.rerun()

    ganho_ano_f = st.session_state.get("g_ano", ANO_NOW)
    ganho_mes_f = st.session_state.get("g_mes", MES_NOW)
    dg_lista = df_ganho[(df_ganho["ano"] == ganho_ano_f) & (df_ganho["mes"] == ganho_mes_f)].copy() if not df_ganho.empty else df_ganho.copy()
    total_liq = dg_lista["valor_liquido"].sum() if not dg_lista.empty else 0.0

    st.markdown(
        f"""
        <div class='ganhos-list-header'>
            <div>
                <div class='ganhos-list-title'>📋 Registros — {MESES_PT[ganho_mes_f]} / {ganho_ano_f}</div>
            </div>
            <div class='ganhos-list-total'>{brl(total_liq)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not dg_lista.empty:
        st.divider()
        for _, r in dg_lista.sort_values("id", ascending=False).iterrows():
            ex = r["extras"] if isinstance(r["extras"], dict) else {}

            if r["tipo_ganho"] == "Salário":
                det_txt = f"Bruto: {brl(float(ex.get('bruto', 0)))} · INSS: -{brl(float(ex.get('inss', 0)))} · IRRF: -{brl(float(ex.get('irrf', 0)))}"
            elif r["tipo_ganho"] == "Investimento":
                det_txt = f"{ex.get('tipo_inv', '')} · {ex.get('onde', '')} · Invest.: {brl(float(ex.get('v_inv', 0)))}"
            elif r["tipo_ganho"] == "Aluguel":
                det_txt = ex.get("imovel", "")
            elif r["tipo_ganho"] == "Freelance":
                det_txt = ex.get("cliente", "")
            else:
                det_txt = ex.get("obs", "")

            icon_r = tipo_icons.get(r["tipo_ganho"], "💰")
            gc1, gc2, gc3, gc4, gc5 = st.columns([0.28, 1.3, 3.5, 1.2, 0.7])

            with gc1:
                st.markdown("<div style='width:9px;height:9px;border-radius:50%;background:#30D158;margin-top:8px'></div>", unsafe_allow_html=True)
            with gc2:
                st.markdown(f"<div style='font-size:.85rem;font-weight:700;color:#FFFFFF;padding-top:4px'>{icon_r} {r['tipo_ganho']}</div>", unsafe_allow_html=True)
            with gc3:
                st.markdown(f"<div style='font-size:.78rem;color:rgba(235,235,245,0.3);padding-top:6px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap'>{det_txt}</div>", unsafe_allow_html=True)
            with gc4:
                st.markdown(f"<div style='font-size:.92rem;font-weight:700;color:#30D158;text-align:right;padding-top:4px;font-variant-numeric:tabular-nums'>{brl(r['valor_liquido'])}</div>", unsafe_allow_html=True)
            with gc5:
                ea, eb = st.columns(2)
                with ea:
                    if st.button("✏️", key=f"ge{r['id']}", help="Editar"):
                        st.session_state.edit_ganho = int(r["id"])
                        for k in ["sal_form_init", "g_ano", "g_mes", "g_tipo", "s_bruto", "s_deps", "s_odesc", "s_oval"]:
                            st.session_state.pop(k, None)
                        st.rerun()
                with eb:
                    if st.button("🗑️", key=f"gd{r['id']}", help="Excluir"):
                        # Registrar histórico antes de excluir
                        snap = {"tipo_ganho": r["tipo_ganho"], "valor_liquido": r["valor_liquido"], "ano": int(r["ano"]), "mes": int(r["mes"])}
                        registrar_historico(username, "ganho", "delete", int(r["id"]), snap)
                        delete_ganho(username, int(r["id"]))
                        st.session_state["msg_ok"] = "🗑️ Ganho excluído com sucesso!"
                        st.rerun()
    else:
        st.markdown(
            f"<div class='ganhos-empty'>Nenhum ganho registrado em {MESES_PT[ganho_mes_f]}/{ganho_ano_f}</div>",
            unsafe_allow_html=True,
        )

    ganho_mes_atual = df_ganho[(df_ganho["ano"] == ANO) & (df_ganho["mes"] == MES)] if not df_ganho.empty else df_ganho
    ganho_ano_atual = df_ganho[df_ganho["ano"] == ANO] if not df_ganho.empty else df_ganho
    if MES > 1 and ganho_mes_atual.empty:
        ant = ganho_ano_atual[ganho_ano_atual["mes"] == (MES - 1)]
        if not ant.empty:
            st.warning(f"⚠️ Você tinha ganhos em {MESES_PT[MES-1]} mas ainda não lançou em {MESES_PT[MES]}.")