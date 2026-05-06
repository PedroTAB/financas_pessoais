"""views/lancamentos.py - Lancamentos."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from utils.color import to_rgba
from utils.charts import spark, bar_mensal, donut, linha_acumulada
from utils.helpers import (
    brl, _parse_brl, _show_feedback,
    MESES_PT, FORMAS_PAGAMENTO,
)
from config import (
    ANO_MINIMO,
)
from data.storage import (
    get_lancamentos, add_lancamento, update_lancamento, delete_lancamento,
    get_ganhos,
    CATEGORIAS_DEBITO, CATEGORIAS_CREDITO,
    TIPOS, _cached_records, registrar_historico,
)

now = datetime.now()
ANO_NOW, MES_NOW = now.year, now.month


def show_lancamentos(username: str):
    # Multi-usuário: username passado explicitamente em cada chamada (sem partial)

    # ── Dados base ───────────────────────────────────────────────────────────
    df_all   = get_lancamentos(username)
    df_ganho = get_ganhos(username)
    ANO = st.session_state.get("ano_sel", ANO_NOW)
    MES = st.session_state.get("mes_sel", MES_NOW)

    _show_feedback()
    st.markdown("""<style>
    .lanc-page-header{display:flex;align-items:flex-start;justify-content:space-between;
        margin-bottom:20px;padding-bottom:16px;border-bottom:1px solid rgba(161,161,170,.1)}
    .lanc-page-title{font-size:1.5rem;font-weight:800;color:#FFFFFF !important;letter-spacing:-.02em;line-height:1.1}
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
    st.markdown("""<div class='lanc-page-header'>
        <div>
            <div class='lanc-page-title'>➕ Lançamentos</div>
            <div class='lanc-page-sub'>Registre créditos e débitos do seu orçamento mensal</div>
        </div>
    </div>""", unsafe_allow_html=True)

    # Linha em edição
    row = None
    eid = st.session_state.edit_lanc
    if eid:
        m = df_all[df_all["id"]==eid]
        if not m.empty:
            row = m.iloc[0]
            # Pré-popular detalhes só na primeira vez que entra em edição
            st.info(f"✏️ Editando #{eid} — {row['descricao']} · Clique em **Cancelar edição** para descartar")

    # ── Formulário principal ──────────────────────────────────────────────────
    def _clear_lanc_form():
        for k in ["l_cat", "l_desc", "l_ano", "l_mes", "l_vf", "l_fp",
                  "l_recorr", "l_recorr_ano", "l_recorr_mes", "l_recorr_eid_loaded"]:
            if k in st.session_state:
                del st.session_state[k]
        if "l_tipo" in st.session_state:
            del st.session_state["l_tipo"]
        st.session_state.edit_lanc = None
        st.session_state.pop("l_form_init", None)
    if "l_tipo" not in st.session_state:
        st.session_state["l_tipo"] = row["tipo"] if row is not None else "Débito"
    if "l_cat" not in st.session_state:
        st.session_state["l_cat"] = row["categoria"] if row is not None else (CATEGORIAS_CREDITO[0] if st.session_state.get("l_tipo", "Débito") == "Crédito" else CATEGORIAS_DEBITO[0])
    if "l_desc" not in st.session_state:
        st.session_state["l_desc"] = row["descricao"] if row is not None else ""
    if "l_ano" not in st.session_state:
        st.session_state["l_ano"] = max(2025, int(row["ano"]) if row is not None else ANO)
    if "l_mes" not in st.session_state:
        st.session_state["l_mes"] = int(row["mes"]) if row is not None else MES
    if "l_vf" not in st.session_state:
        st.session_state["l_vf"] = f"{float(row['valor']):,.2f}".replace(",","X").replace(".",",").replace("X",".") if row is not None else ""
    if "l_fp" not in st.session_state:
        st.session_state["l_fp"] = row["forma_pagamento"] if row is not None and "forma_pagamento" in row and str(row["forma_pagamento"]).strip() else FORMAS_PAGAMENTO[0]
    # Pré-popular recorrência: reler do grupo_id apenas na PRIMEIRA vez que entra neste eid
    # Usa flag "l_recorr_eid_loaded" para não sobrescrever mudanças do usuário nos reruns
    _recorr_loaded_eid = st.session_state.get("l_recorr_eid_loaded", None)
    if eid and row is not None and _recorr_loaded_eid != eid:
        # Primeira vez editando este registro: ler grupo_id e popular recorrência
        _gid = str(row.get("grupo_id", "") or "")
        if "|" in _gid:
            _parts = _gid.split("|")
            try:
                _r_ano = int(_parts[1]); _r_mes = int(_parts[2])
                st.session_state["l_recorr"]     = True
                st.session_state["l_recorr_ano"] = _r_ano
                st.session_state["l_recorr_mes"] = _r_mes
            except Exception:
                st.session_state["l_recorr"] = False
                st.session_state.setdefault("l_recorr_ano", ANO_NOW)
                st.session_state.setdefault("l_recorr_mes", MES_NOW)
        else:
            st.session_state["l_recorr"] = False
            st.session_state.setdefault("l_recorr_ano", ANO_NOW)
            st.session_state.setdefault("l_recorr_mes", MES_NOW)
        # Marcar que já carregamos para este eid — não sobrescrever em reruns seguintes
        st.session_state["l_recorr_eid_loaded"] = eid
    elif not eid and "l_recorr" not in st.session_state:
        st.session_state["l_recorr"] = False
        st.session_state.setdefault("l_recorr_ano", ANO_NOW)
        st.session_state.setdefault("l_recorr_mes", MES_NOW)

    # ── Seletores reativos + form dentro de container ───────────────────────────
    with st.container(border=True):

        # Linha 1: período + tipo
        _lc1, _lc2, _lc3 = st.columns(3)
        with _lc1:
            _anos_l = list(range(2025, ANO_NOW + 1))
            ano_f = st.selectbox("Ano", _anos_l, format_func=str, key="l_ano")
        with _lc2:
            mes_f = st.selectbox("Mês", list(MESES_PT.keys()),
                                 format_func=lambda x: MESES_PT[x], key="l_mes")
        with _lc3:
            tipo_inp = st.selectbox("Tipo", TIPOS, key="l_tipo")

        cats_disp = CATEGORIAS_CREDITO if tipo_inp == "Crédito" else CATEGORIAS_DEBITO
        _cat_default = CATEGORIAS_CREDITO[0] if tipo_inp == "Crédito" else CATEGORIAS_DEBITO[0]
        if st.session_state.get("l_cat") not in cats_disp:
            st.session_state["l_cat"] = _cat_default

        # Badge do tipo selecionado
        _badge_cls = "lanc-tipo-credito" if tipo_inp == "Crédito" else "lanc-tipo-debito"
        _badge_icon = "💚" if tipo_inp == "Crédito" else "🔴"
        st.markdown(f"<div class='lanc-tipo-badge {_badge_cls}'>{_badge_icon} {tipo_inp}</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

        # Linha 2: descrição + categoria (linha inteira)
        fd1, fd2 = st.columns([2, 1])
        with fd1:
            desc_inp = st.text_input("Descrição", key="l_desc", placeholder="Ex: Aluguel, Mercado, Farmácia...")
        with fd2:
            cat_inp = st.selectbox("Categoria", cats_disp, key="l_cat")

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

        # Linha 3: forma de pagamento + valor
        ff1, ff2 = st.columns([1, 1])
        with ff1:
            fp_inp = st.selectbox("Forma de Pagamento", FORMAS_PAGAMENTO, key="l_fp")
        with ff2:
            vf_raw = st.text_input("Valor (R$)", placeholder="Ex: 250,00", key="l_vf")
            valor_f = _parse_brl(vf_raw)

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # Recorrência — expander com info visual quando já marcada
        # Recorrência — lida com o state diretamente para mostrar valores corretos
        _saved_recorr = st.session_state.get("l_recorr", False)
        _saved_r_ano  = st.session_state.get("l_recorr_ano", ANO_NOW)
        _saved_r_mes  = st.session_state.get("l_recorr_mes", MES_NOW)
        anos_rec = list(range(ANO_NOW, ANO_NOW + 6))
        if _saved_r_ano not in anos_rec:
            anos_rec = sorted(set([_saved_r_ano] + anos_rec))
        _meses_rec = list(range(1, 13))
        _recorr_label = (f"🔁 Recorrência ativa — até {MESES_PT.get(_saved_r_mes,'?')}/{_saved_r_ano}"
                         if _saved_recorr else "🔁 Recorrência (opcional)")
        with st.expander(_recorr_label, expanded=_saved_recorr):
            usar_recorr = st.checkbox("Repetir este lançamento mensalmente até a data:",
                                      value=_saved_recorr, key="l_recorr")
            if usar_recorr:
                st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
                rc1, rc2 = st.columns(2)
                _idx_ano = anos_rec.index(_saved_r_ano) if _saved_r_ano in anos_rec else 0
                _idx_mes = (_saved_r_mes - 1) if 1 <= _saved_r_mes <= 12 else (MES_NOW - 1)
                with rc1:
                    recorr_ate_ano = st.selectbox("Até o Ano", anos_rec,
                        index=_idx_ano, format_func=str, key="l_recorr_ano")
                with rc2:
                    recorr_ate_mes = st.selectbox("Até o Mês", _meses_rec,
                        index=_idx_mes, format_func=lambda x: MESES_PT[x], key="l_recorr_mes")
                _r_a = recorr_ate_ano
                _r_m = recorr_ate_mes
                st.markdown(f"<div style='font-size:.78rem;color:#30D158;margin-top:6px'>✓ Repetido de {MESES_PT[mes_f]}/{ano_f} até {MESES_PT.get(_r_m,'?')}/{_r_a}</div>", unsafe_allow_html=True)
            else:
                recorr_ate_ano = _saved_r_ano
                recorr_ate_mes = _saved_r_mes
        usar_recorr = st.session_state.get("l_recorr", False)
        recorr_ate_ano = st.session_state.get("l_recorr_ano", _saved_r_ano)
        recorr_ate_mes = st.session_state.get("l_recorr_mes", _saved_r_mes)

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        bc1, bc2 = st.columns(2)
        with bc1: salvar = st.button("💾 Salvar", width="stretch", key="lanc_salvar")
        _lbl_canc_lanc = "✕ Cancelar edição" if st.session_state.edit_lanc else "↺ Limpar campos"
        with bc2: cancelar = st.button(_lbl_canc_lanc, width="stretch", key="lanc_cancelar", on_click=_clear_lanc_form)

    if cancelar:
        st.rerun()

    if salvar:
        if not desc_inp.strip():
            st.error("Informe a descrição!")
        else:
            usar_r = usar_recorr
            if eid and row is not None:
                # Identificar grupo antigo pelo grupo_id salvo
                _old_gid = str(row.get("grupo_id", "") or "")
                _new_gid = f"recorr|{recorr_ate_ano}|{recorr_ate_mes}" if usar_r else ""

                if usar_r:
                    # Edição recorrente: calcular quais meses já existem no grupo
                    df_now = get_lancamentos(username)
                    _grupo_existente = df_now[
                        df_now["grupo_id"].astype(str).str.startswith("recorr|") &
                        (df_now["descricao"] == str(row["descricao"])) &
                        (df_now["categoria"] == str(row["categoria"])) &
                        (df_now["tipo"] == str(row["tipo"]))
                    ] if not df_now.empty else pd.DataFrame()

                    # Montar set de meses que DEVEM existir (novo range)
                    _meses_novos = set()
                    _cur_a, _cur_m = ano_f, mes_f
                    while (_cur_a, _cur_m) <= (recorr_ate_ano, recorr_ate_mes):
                        _meses_novos.add((_cur_a, _cur_m))
                        _cur_m += 1
                        if _cur_m > 12: _cur_m = 1; _cur_a += 1

                    # Montar set de meses que JÁ EXISTEM no grupo
                    _meses_existentes = {}
                    if not _grupo_existente.empty:
                        for _, _gr in _grupo_existente.iterrows():
                            _meses_existentes[( int(_gr["ano"]), int(_gr["mes"]) )] = int(_gr["id"])

                    # Excluir meses que saíram do range
                    _excluidos = 0
                    for (_ea, _em), _eid in _meses_existentes.items():
                        if (_ea, _em) not in _meses_novos:
                            # Registrar histórico antes de excluir
                            snap = {"descricao": desc_inp.strip(), "categoria": cat_inp, "tipo": tipo_inp, "valor": valor_f, "ano": _ea, "mes": _em}
                            registrar_historico(username, "lancamento", "delete", _eid, snap)
                            delete_lancamento(username, _eid)
                            _excluidos += 1

                    # Inserir/atualizar meses do novo range
                    _inseridos, _atualizados = 0, 0
                    for (_na, _nm) in sorted(_meses_novos):
                        if (_na, _nm) in _meses_existentes:
                            update_lancamento(username, _meses_existentes[(_na, _nm)], _na, _nm,
                                desc_inp.strip(), cat_inp, tipo_inp, valor_f, _new_gid, fp_inp)
                            registrar_historico(username, "lancamento", "update", _meses_existentes[(_na, _nm)], 
                                {"descricao": desc_inp.strip(), "categoria": cat_inp, "tipo": tipo_inp, "valor": valor_f, "ano": _na, "mes": _nm})
                            _atualizados += 1
                        else:
                            ok, _ = add_lancamento(username, _na, _nm, desc_inp.strip(),
                                cat_inp, tipo_inp, valor_f, _new_gid, fp_inp)
                            if ok:
                                df_novo = get_lancamentos(username)
                                novo = df_novo[(df_novo["ano"] == _na) & (df_novo["mes"] == _nm) & (df_novo["descricao"] == desc_inp.strip())]
                                if not novo.empty:
                                    novo_id = int(novo.iloc[0]["id"])
                                    registrar_historico(username, "lancamento", "create", novo_id,
                                        {"descricao": desc_inp.strip(), "categoria": cat_inp, "tipo": tipo_inp, "valor": valor_f, "ano": _na, "mes": _nm})
                            _inseridos += 1

                    _cached_records.clear()
                    st.session_state.edit_lanc = None
                    _clear_lanc_form()
                    st.session_state["_msg_ok"] = (
                        f"✅ Recorrência atualizada: {_atualizados} atualizados, "
                        f"{_inseridos} adicionados, {_excluidos} removidos."
                    )
                    st.rerun()
                else:
                    # Edição simples (sem recorrência)
                    ok, err = update_lancamento(username, eid, ano_f, mes_f, desc_inp.strip(),
                                      cat_inp, tipo_inp, valor_f, _new_gid, fp_inp)
                    if ok:
                        registrar_historico(username, "lancamento", "update", eid, 
                            {"descricao": desc_inp.strip(), "categoria": cat_inp, "tipo": tipo_inp, "valor": valor_f, "ano": ano_f, "mes": mes_f})
                        _cached_records.clear()
                        st.session_state.edit_lanc = None
                        _clear_lanc_form()
                        st.session_state["_msg_ok"] = "✅ Lançamento atualizado com sucesso!"
                        st.rerun()
                    else:
                        st.error(err or "Erro ao atualizar lançamento.")
            elif usar_r and recorr_ate_ano and recorr_ate_mes:
                # Inserir do mês/ano do form até o mês/ano alvo
                cur_a, cur_m = ano_f, mes_f
                count_new, count_upd = 0, 0
                while (cur_a, cur_m) <= (recorr_ate_ano, recorr_ate_mes):
                    df_now = get_lancamentos(username)
                    existe = df_now[
                        (df_now["ano"]==cur_a) & (df_now["mes"]==cur_m) &
                        (df_now["descricao"]==desc_inp.strip()) &
                        (df_now["categoria"]==cat_inp) &
                        (df_now["tipo"]==tipo_inp)
                    ] if not df_now.empty else pd.DataFrame()
                    if not existe.empty:
                        _gid_recorr = f"recorr|{recorr_ate_ano}|{recorr_ate_mes}"
                        ok_u, err_u = update_lancamento(username, int(existe.iloc[0]["id"]), cur_a, cur_m,
                                         desc_inp.strip(), cat_inp, tipo_inp, valor_f, _gid_recorr, fp_inp)
                        if not ok_u:
                            st.error(err_u or f"Erro ao atualizar {MESES_PT[cur_m]}/{cur_a}")
                            st.stop()
                        registrar_historico(username, "lancamento", "update", int(existe.iloc[0]["id"]),
                            {"descricao": desc_inp.strip(), "categoria": cat_inp, "tipo": tipo_inp, "valor": valor_f, "ano": cur_a, "mes": cur_m})
                        count_upd += 1
                    else:
                        _gid_recorr = f"recorr|{recorr_ate_ano}|{recorr_ate_mes}"
                        ok_a, err_a = add_lancamento(username, cur_a, cur_m, desc_inp.strip(),
                                      cat_inp, tipo_inp, valor_f, _gid_recorr, fp_inp)
                        if not ok_a:
                            st.error(err_a or f"Erro ao salvar {MESES_PT[cur_m]}/{cur_a}")
                            st.stop()
                        # Registrar histórico do novo registro
                        df_novo = get_lancamentos(username)
                        novo = df_novo[(df_novo["ano"] == cur_a) & (df_novo["mes"] == cur_m) & (df_novo["descricao"] == desc_inp.strip())]
                        if not novo.empty:
                            novo_id = int(novo.iloc[0]["id"])
                            registrar_historico(username, "lancamento", "create", novo_id,
                                {"descricao": desc_inp.strip(), "categoria": cat_inp, "tipo": tipo_inp, "valor": valor_f, "ano": cur_a, "mes": cur_m})
                        count_new += 1
                    cur_m += 1
                    if cur_m > 12:
                        cur_m = 1; cur_a += 1
                _cached_records.clear()
                _clear_lanc_form()
                st.session_state["_msg_ok"] = f"✅ {count_new} meses inseridos, {count_upd} atualizados!"
                st.rerun()
            else:
                ok, err = add_lancamento(username, ano_f, mes_f, desc_inp.strip(),
                               cat_inp, tipo_inp, valor_f, "", fp_inp)
                if ok:
                    # Registrar histórico do novo registro
                    df_novo = get_lancamentos(username)
                    novo = df_novo[(df_novo["ano"] == ano_f) & (df_novo["mes"] == mes_f) & (df_novo["descricao"] == desc_inp.strip())]
                    if not novo.empty:
                        novo_id = int(novo.iloc[0]["id"])
                        registrar_historico(username, "lancamento", "create", novo_id,
                            {"descricao": desc_inp.strip(), "categoria": cat_inp, "tipo": tipo_inp, "valor": valor_f, "ano": ano_f, "mes": mes_f})
                    _cached_records.clear()
                    _clear_lanc_form()
                    st.session_state["_msg_ok"] = "✅ Lançamento salvo com sucesso!"
                    st.rerun()
                else:
                    st.error(err or "Erro ao salvar lançamento.")
    # ── Lista do mês ──────────────────────────────────────────────────────────
    st.divider()
    _lanc_ano_f = st.session_state.get("l_ano", ANO_NOW)
    _lanc_mes_f = st.session_state.get("l_mes", MES_NOW)
    df_lista = df_all[(df_all["ano"]==_lanc_ano_f) & (df_all["mes"]==_lanc_mes_f)].copy() if not df_all.empty else df_all.copy()
    _cred_tot = df_lista[df_lista["tipo"]=="Crédito"]["valor"].sum()
    _deb_tot  = df_lista[df_lista["tipo"]=="Débito"]["valor"].sum()
    st.markdown(f"""<div class='lanc-list-header'>
        <div class='lanc-list-title'>📋 {MESES_PT[_lanc_mes_f]} / {_lanc_ano_f}</div>
        <div class='lanc-list-totals'>
            <span class='lanc-tot-cred'>💚 {brl(_cred_tot)}</span>
            <span class='lanc-tot-deb'>🔴 {brl(_deb_tot)}</span>
        </div>
    </div>""", unsafe_allow_html=True)

    if not df_lista.empty:
        df_s = df_lista.sort_values("id", ascending=False)

        # Cabeçalho
        h1,h2,h3,h4,h5,h6,h7 = st.columns([0.3, 2.4, 1.4, 1.0, 1.6, 1.2, 0.7])
        h1.markdown("<span style='font-size:.72rem;color:rgba(235,235,245,0.3);text-transform:uppercase;letter-spacing:.08em'></span>", unsafe_allow_html=True)
        h2.markdown("<span style='font-size:.72rem;color:rgba(235,235,245,0.3);text-transform:uppercase;letter-spacing:.08em'>Descrição</span>", unsafe_allow_html=True)
        h3.markdown("<span style='font-size:.72rem;color:rgba(235,235,245,0.3);text-transform:uppercase;letter-spacing:.08em'>Categoria</span>", unsafe_allow_html=True)
        h4.markdown("<span style='font-size:.72rem;color:rgba(235,235,245,0.3);text-transform:uppercase;letter-spacing:.08em'>Tipo</span>", unsafe_allow_html=True)
        h5.markdown("<span style='font-size:.72rem;color:rgba(235,235,245,0.3);text-transform:uppercase;letter-spacing:.08em'>Forma Pgto</span>", unsafe_allow_html=True)
        h6.markdown("<span style='font-size:.72rem;color:rgba(235,235,245,0.3);text-transform:uppercase;letter-spacing:.08em'>Valor</span>", unsafe_allow_html=True)
        h7.markdown("<span style='font-size:.72rem;color:rgba(235,235,245,0.3);text-transform:uppercase;letter-spacing:.08em'>Ações</span>", unsafe_allow_html=True)
        st.markdown("<hr style='margin:.2rem 0 .4rem;opacity:.15'>", unsafe_allow_html=True)

        for _, r in df_s.iterrows():
            ri1,ri2,ri3,ri4,ri5,ri6,ri7 = st.columns([0.3, 2.4, 1.4, 1.0, 1.6, 1.2, 0.7])
            with ri1:
                cor = "#30D158" if r["tipo"]=="Crédito" else "#FF453A"
                st.markdown(f"<div style='width:10px;height:10px;border-radius:50%;background:{cor};margin-top:6px'></div>", unsafe_allow_html=True)
            with ri2:
                st.markdown(f"<div style='font-weight:600;padding-top:2px'>{r['descricao']}</div>", unsafe_allow_html=True)
                _detalhes = r.get("detalhes", []) if hasattr(r, "get") else []
                if isinstance(_detalhes, list) and _detalhes:
                    tot_d = sum(d.get("valor", 0) for d in _detalhes if isinstance(d, dict))
                    with st.expander(f"  ＋ {len(_detalhes)} item(s) · {brl(tot_d)}", expanded=False):
                        for d in _detalhes:
                            if isinstance(d, dict):
                                st.markdown(
                                    f"<div style='padding:.15rem 0 .15rem 1.2rem;font-size:.83rem;color:rgba(235,235,245,0.4);border-left:1.5px solid rgba(255,255,255,0.1)'><b>{d.get('desc','Item')}</b> <span style='color:rgba(235,235,245,0.2);margin:0 .3rem'>—</span> {brl(d.get('valor',0))}</div>",
                                    unsafe_allow_html=True)
            ri3.markdown(f"<div style='padding-top:6px;font-size:.88rem'>{r['categoria']}</div>", unsafe_allow_html=True)
            ri4.markdown(f"<div style='padding-top:6px;font-size:.88rem'>{r['tipo']}</div>", unsafe_allow_html=True)
            _fp = str(r.get("forma_pagamento", "") or "—") if hasattr(r, "get") else "—"
            ri5.markdown(f"<div style='padding-top:6px;font-size:.88rem;color:rgba(235,235,245,0.6)'>{_fp}</div>", unsafe_allow_html=True)
            ri6.markdown(f"<div style='padding-top:6px;font-weight:600;color:{'#30D158' if r['tipo']=='Crédito' else '#FF453A'}'>{brl(r['valor'])}</div>", unsafe_allow_html=True)
            with ri7:
                ea, eb = st.columns(2)
                with ea:
                    if st.button("✏️", key=f"el{r['id']}", help="Editar"):
                        st.session_state.edit_lanc = int(r["id"])
                        # Limpar todas as keys do form + flag de loaded para forçar releitura do grupo_id
                        for _k in ["l_tipo","l_cat","l_desc","l_ano","l_mes","l_vf","l_fp",
                                   "l_form_init","l_recorr","l_recorr_ano","l_recorr_mes",
                                   "l_recorr_eid_loaded"]:
                            st.session_state.pop(_k, None)
                        st.rerun()
                with eb:
                    if st.button("🗑️", key=f"dl{r['id']}", help="Excluir"):
                        # Registrar histórico antes de excluir
                        snap = {"descricao": r["descricao"], "categoria": r["categoria"], "tipo": r["tipo"], "valor": float(r["valor"]), "ano": int(r["ano"]), "mes": int(r["mes"])}
                        registrar_historico(username, "lancamento", "delete", int(r["id"]), snap)
                        delete_lancamento(username, int(r["id"]))
                        _cached_records.clear()
                        st.session_state["_msg_ok"] = "🗑️ Lançamento excluído com sucesso!"
                        st.rerun()
            st.markdown("<div style='height:1px;background:rgba(255,255,255,.05);margin:.15rem 0'></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='lanc-empty'>Nenhum lançamento em {MESES_PT[_lanc_mes_f]}/{_lanc_ano_f}.<br><span style='font-size:.78rem'>Use o formulário acima para adicionar.</span></div>", unsafe_allow_html=True)