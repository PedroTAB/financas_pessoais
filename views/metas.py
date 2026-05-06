"""views/metas.py - Metas e Reservas."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, date
import calendar as _cal
from utils.helpers import brl
from data.metas_storage import (
    get_metas, add_meta, update_meta, delete_meta, update_meta_valor_atual,
    TIPOS_META, ICONES_META,
)

_MESES_PT = {
    0: "Sem prazo", 1: "Janeiro", 2: "Fevereiro", 3: "Marco", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}

_ESTILOS = """<style>
.meta-card{background:#1C1C1E;border:0.5px solid rgba(255,255,255,0.08);
    border-radius:18px;padding:20px 22px 16px;position:relative;overflow:hidden}
.meta-card-done{background:linear-gradient(135deg,#0D2818 0%,#1C1C1E 60%);
    border:0.5px solid rgba(48,209,88,0.25)}
.meta-card-accent{position:absolute;top:0;left:0;right:0;height:3px;border-radius:18px 18px 0 0}
.meta-icone{font-size:1.6rem;margin-bottom:8px;line-height:1}
.meta-nome{font-size:1rem;font-weight:700;color:#FFFFFF;margin-bottom:2px}
.meta-tipo{font-size:.7rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
    color:rgba(235,235,245,0.3);margin-bottom:14px}
.meta-valores{display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:10px}
.meta-atual{font-size:1.3rem;font-weight:800;letter-spacing:-.03em}
.meta-alvo{font-size:.8rem;color:rgba(235,235,245,0.4);text-align:right}
.meta-bar-bg{height:8px;background:rgba(255,255,255,0.08);border-radius:99px;overflow:hidden;margin-bottom:8px}
.meta-bar-fill{height:100%;border-radius:99px}
.meta-footer{display:flex;justify-content:space-between;align-items:center;
    font-size:.75rem;color:rgba(235,235,245,0.3);margin-top:4px}
.meta-badge{display:inline-flex;align-items:center;padding:2px 9px;border-radius:999px;
    font-size:.72rem;font-weight:700;letter-spacing:.05em}
.meta-badge-ok{background:rgba(48,209,88,0.15);color:#30D158;border:0.5px solid rgba(48,209,88,0.2)}
.meta-badge-warn{background:rgba(255,159,10,0.15);color:#FF9F0A;border:0.5px solid rgba(255,159,10,0.2)}
.meta-badge-done{background:rgba(48,209,88,0.2);color:#30D158;border:0.5px solid rgba(48,209,88,0.4)}
.meta-por-dia{font-size:.76rem;color:rgba(235,235,245,0.4);margin-top:6px}
.meta-kpi-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px}
.meta-kpi{background:#1C1C1E;border:0.5px solid rgba(255,255,255,0.08);
    border-radius:14px;padding:14px 16px}
.meta-kpi-lbl{font-size:.68rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
    color:rgba(235,235,245,0.3);margin-bottom:4px}
.meta-kpi-val{font-size:1.2rem;font-weight:800;color:#FFFFFF;letter-spacing:-.02em}
.meta-kpi-sub{font-size:.72rem;color:rgba(235,235,245,0.3);margin-top:2px}
.arq-row{display:flex;align-items:center;gap:10px;padding:10px 14px;
    background:#1C1C1E;border:0.5px solid rgba(255,255,255,0.06);
    border-radius:12px;margin-bottom:8px;opacity:.65}
.arq-info{flex:1;font-size:.85rem;color:rgba(235,235,245,0.7)}
.arq-val{font-size:.78rem;color:rgba(235,235,245,0.4);white-space:nowrap}
</style>"""


# ── Helpers ────────────────────────────────────────────────────────────────
def _pct_meta(row):
    try:
        alvo = float(row["valor_alvo"])
        return min(float(row["valor_atual"]) / alvo * 100, 100) if alvo > 0 else 0.0
    except Exception:
        return 0.0


def _fmt_brl(val):
    try:
        return f"{float(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "0,00"


def _parse_brl(s):
    try:
        return float(str(s).strip().replace(".", "").replace(",", "."))
    except Exception:
        raise ValueError(f"Valor invalido: '{s}'. Use o formato 1.500,00")



def _brl_md(val) -> str:
    """brl() com $ escapado para uso em st.caption / st.markdown sem unsafe_allow_html."""
    return brl(val).replace("$", r"\$")

def _dias_restantes(prazo_ano: int, prazo_mes: int) -> int:
    if prazo_ano <= 0 or prazo_mes <= 0:
        return -1
    try:
        ultimo = _cal.monthrange(int(prazo_ano), int(prazo_mes))[1]
        return max((date(int(prazo_ano), int(prazo_mes), ultimo) - date.today()).days, 0)
    except Exception:
        return -1


def _ss_counter(key: str) -> int:
    return st.session_state.setdefault("_meta_counters", {}).get(key, 0)


def _ss_counter_inc(key: str):
    c = st.session_state.setdefault("_meta_counters", {})
    c[key] = c.get(key, 0) + 1


def _card_html(row, concluida: bool = False) -> str:
    pct   = _pct_meta(row)
    falta = max(float(row["valor_alvo"]) - float(row["valor_atual"]), 0)
    cor   = str(row["cor"]) if row["cor"] else "#30D158"
    icone = str(row["icone"]) if row["icone"] else "🎯"
    prazo = ""
    try:
        if int(row["prazo_ano"]) > 0 and int(row["prazo_mes"]) > 0:
            prazo = f"Prazo: {_MESES_PT.get(int(row['prazo_mes']), '')} {int(row['prazo_ano'])}"
    except Exception:
        pass

    if concluida:
        badge_html = "<span class='meta-badge meta-badge-done'>✅ Concluida</span>"
        badge_right = "100%"
    else:
        badge_cls  = "meta-badge-ok" if pct >= 70 else "meta-badge-warn"
        badge_html = f"<span class='meta-badge {badge_cls}'>{pct:.1f}% alcancado</span>"
        badge_right = prazo

    card_cls = "meta-card meta-card-done" if concluida else "meta-card"

    dias   = _dias_restantes(int(row["prazo_ano"]), int(row["prazo_mes"]))
    pd_html = ""
    if not concluida and falta > 0 and dias > 0:
        pd_html = (
            f"<div class='meta-por-dia'>"
            f"≈ {brl(falta / dias)}/dia &nbsp;·&nbsp; {dias} dias restantes"
            f"</div>"
        )

    return (
        f"<div class='{card_cls}'>"
        f"<div class='meta-card-accent' style='background:{cor}'></div>"
        f"<div class='meta-icone'>{icone}</div>"
        f"<div class='meta-nome'>{row['nome']}</div>"
        f"<div class='meta-tipo'>{row['tipo']}</div>"
        f"<div class='meta-valores'>"
        f"<div class='meta-atual' style='color:{cor}'>{brl(float(row['valor_atual']))}</div>"
        f"<div class='meta-alvo'>Meta: {brl(float(row['valor_alvo']))}"
        + (f"<br>Falta: {brl(falta)}" if not concluida else "") +
        f"</div></div>"
        f"<div class='meta-bar-bg'>"
        f"<div class='meta-bar-fill' style='width:{pct:.1f}%;background:{cor}'></div></div>"
        f"<div class='meta-footer'>{badge_html}<span>{badge_right}</span></div>"
        f"{pd_html}"
        f"</div>"
    )


def _render_expander_meta(row, username, brl):
    """Expander de aporte + editar para uma meta."""
    _rid    = str(row["id"])
    _ap_cnt = _ss_counter(f"ap_{_rid}")
    _ed_cnt = _ss_counter(f"ed_{_rid}")
    _now    = datetime.now()

    with st.expander("💸 Aporte / ✏️ Editar meta"):
        _tab_ap, _tab_ed = st.tabs(["💸 Aporte rápido", "✏️ Editar meta"])

        with _tab_ap:
            _falta_r = max(float(row["valor_alvo"]) - float(row["valor_atual"]), 0)
            _dias_r  = _dias_restantes(int(row["prazo_ano"]), int(row["prazo_mes"]))
            if _falta_r > 0 and _dias_r > 0:
                st.caption(
                    f"Falta {_brl_md(_falta_r)} · "
                    f"Guardar {_brl_md(_falta_r / _dias_r)}/dia · "
                    f"{_dias_r} dias restantes"
                )
            elif _falta_r > 0:
                st.caption(f"Falta {_brl_md(_falta_r)} · Sem prazo definido")

            _ap_raw = st.text_input(
                "Valor do aporte (R$)", placeholder="Ex: 500,00",
                key=f"ap_{_rid}_{_ap_cnt}",
            )
            _ab1, _ab2 = st.columns(2)
            with _ab1:
                if st.button("✅ Confirmar", key=f"btn_ap_{_rid}",
                             width='stretch'):
                    try:
                        _ap_n = _parse_brl(_ap_raw)
                        if _ap_n <= 0:
                            st.error("Valor deve ser maior que zero.")
                        else:
                            _novo     = float(row["valor_atual"]) + _ap_n
                            _concluiu = _novo >= float(row["valor_alvo"])
                            if _concluiu:
                                # Arquiva automaticamente ao concluir
                                _ok, _err = update_meta(
                                    int(row["id"]), username,
                                    str(row["nome"]), str(row["tipo"]),
                                    float(row["valor_alvo"]), float(_novo),
                                    int(row["prazo_ano"]), int(row["prazo_mes"]),
                                    str(row["cor"]), str(row["icone"]), False,
                                )
                                if _ok:
                                    _ss_counter_inc(f"ap_{_rid}")
                                    _ss_counter_inc(f"ed_{_rid}")
                                    st.session_state["_meta_balloon"]   = True
                                    st.session_state["_meta_concluida"] = str(row["nome"])
                                    st.rerun()
                                else:
                                    st.error(f"Erro: {_err}")
                            else:
                                _ok, _err = update_meta_valor_atual(int(row["id"]), _novo)
                                if _ok:
                                    _ss_counter_inc(f"ap_{_rid}")
                                    _ss_counter_inc(f"ed_{_rid}")
                                    st.success(f"Aporte de {brl(_ap_n)} registrado!")
                                    st.rerun()
                                else:
                                    st.error(f"Erro: {_err}")
                    except ValueError as _ve:
                        st.error(str(_ve))
            with _ab2:
                if st.button("🔄 Zerar", key=f"btn_zer_{_rid}",
                             width='stretch'):
                    _ok, _err = update_meta_valor_atual(int(row["id"]), 0.0)
                    if _ok:
                        _ss_counter_inc(f"ap_{_rid}")
                        _ss_counter_inc(f"ed_{_rid}")
                        st.rerun()
                    else:
                        st.error(f"Erro: {_err}")

        with _tab_ed:
            _e_nome = st.text_input("Nome", value=str(row["nome"]),
                                    key=f"en_{_rid}_{_ed_cnt}")
            _e_tipo = st.selectbox("Tipo", TIPOS_META,
                index=TIPOS_META.index(row["tipo"]) if row["tipo"] in TIPOS_META else 0,
                key=f"et_{_rid}_{_ed_cnt}")
            _e_alvo_raw = st.text_input("Valor alvo (R$)",
                value=_fmt_brl(row["valor_alvo"]), key=f"ea_{_rid}_{_ed_cnt}")
            _e_atual_raw = st.text_input("Valor acumulado (R$)",
                value=_fmt_brl(row["valor_atual"]), key=f"eac_{_rid}_{_ed_cnt}",
                help="Prefira usar o Aporte rápido.")
            _ec1, _ec2 = st.columns(2)
            with _ec1:
                _prazo_ano_val = int(row["prazo_ano"]) if int(row["prazo_ano"]) > 0 else _now.year
                _e_ano = st.number_input("Prazo - Ano", min_value=0, max_value=2100,
                    value=_prazo_ano_val, key=f"ey_{_rid}_{_ed_cnt}")
            with _ec2:
                _prazo_mes_idx = int(row["prazo_mes"]) if 0 <= int(row["prazo_mes"]) <= 12 else 0
                _e_mes = st.selectbox("Prazo - Mes",
                    options=list(range(0, 13)),
                    format_func=lambda x: _MESES_PT.get(x, ""),
                    index=_prazo_mes_idx, key=f"em_{_rid}_{_ed_cnt}")
            _e_icone = st.selectbox("Icone", ICONES_META,
                index=ICONES_META.index(row["icone"]) if row["icone"] in ICONES_META else 0,
                key=f"ei_{_rid}_{_ed_cnt}")
            _e_cor   = st.color_picker("Cor",
                value=str(row["cor"]) if row["cor"] else "#30D158",
                key=f"ec_{_rid}_{_ed_cnt}")
            _e_ativa = st.checkbox("Meta ativa", value=bool(row["ativa"]),
                                   key=f"eav_{_rid}_{_ed_cnt}")
            _eb1, _eb2 = st.columns(2)
            with _eb1:
                if st.button("💾 Salvar", key=f"save_{_rid}", width='stretch'):
                    try:
                        _an  = _parse_brl(_e_alvo_raw)
                        _acn = _parse_brl(_e_atual_raw)
                        _ok, _err = update_meta(
                            int(row["id"]), username,
                            _e_nome, _e_tipo, _an, _acn,
                            int(_e_ano), int(_e_mes),
                            _e_cor, _e_icone, _e_ativa,
                        )
                        if _ok:
                            _ss_counter_inc(f"ap_{_rid}")
                            _ss_counter_inc(f"ed_{_rid}")
                            st.success("Meta atualizada!")
                            st.rerun()
                        else:
                            st.error(f"Erro: {_err}")
                    except ValueError as _ve:
                        st.error(str(_ve))
            with _eb2:
                if st.button("🗑 Excluir", key=f"del_{_rid}",
                             width='stretch', type="primary"):
                    _ok, _err = delete_meta(int(row["id"]))
                    if _ok:
                        st.rerun()
                    else:
                        st.error(f"Erro: {_err}")


# ── View principal ─────────────────────────────────────────────────────────
def show_metas(username: str):
    # Animacao (executada antes de qualquer rerun)
    if st.session_state.get("_meta_balloon", False):
        st.balloons()
        st.session_state["_meta_balloon"] = False

    df = get_metas(username)

    # Separar em 3 grupos
    if df.empty:
        df_em_prog  = pd.DataFrame()
        df_concl    = pd.DataFrame()
        df_arq      = pd.DataFrame()
    else:
        _ativas = df[df["ativa"] == True].copy()
        _inativ = df[df["ativa"] == False].copy()
        # Concluidas = inativas onde valor_atual >= valor_alvo
        _mask_concl = (
            _inativ["valor_atual"].astype(float) >= _inativ["valor_alvo"].astype(float)
        )
        df_em_prog = _ativas.reset_index(drop=True)
        df_concl   = _inativ[_mask_concl].reset_index(drop=True)
        df_arq     = _inativ[~_mask_concl].reset_index(drop=True)

    _now    = datetime.now()
    ANO_NOW = _now.year
    MES_NOW = _now.month

    st.markdown(_ESTILOS, unsafe_allow_html=True)

    # ── Header ────────────────────────────────────────────────────────────
    _hc1, _hc2 = st.columns([3, 1])
    with _hc1:
        st.markdown(
            "<div style='font-size:1.5rem;font-weight:800;color:#FFFFFF;"
            "letter-spacing:-.02em;margin-bottom:4px'>🎯 Metas e Reservas</div>"
            "<div style='font-size:.82rem;color:rgba(235,235,245,0.3);margin-bottom:16px'>"
            "Acompanhe seus objetivos financeiros</div>",
            unsafe_allow_html=True,
        )
    with _hc2:
        _toggled = st.session_state.get("show_form_meta", False)
        if st.button("✕ Fechar" if _toggled else "＋ Nova Meta",
                     width='stretch', key="btn_nova_meta"):
            st.session_state["show_form_meta"] = not _toggled
            st.rerun()

    # Mensagem de conclusao (aparece apos balloons)
    _nome_concl = st.session_state.pop("_meta_concluida", None)
    if _nome_concl:
        st.success(f"🎉 Parabens! A meta **{_nome_concl}** foi concluida!")

    # ── Formulario Nova Meta (logo abaixo do header) ──────────────────────
    if st.session_state.get("show_form_meta", False):
        with st.form("form_nova_meta", clear_on_submit=True):
            st.markdown(
                "<div style='font-size:.75rem;font-weight:700;letter-spacing:.1em;"
                "text-transform:uppercase;color:rgba(235,235,245,0.4);margin-bottom:8px'>"
                "NOVA META</div>", unsafe_allow_html=True,
            )
            _fc1, _fc2, _fc3 = st.columns(3)
            with _fc1:
                _f_nome = st.text_input("Nome *", placeholder="Ex: Reserva de Emergencia")
                _f_tipo = st.selectbox("Tipo *", TIPOS_META)
            with _fc2:
                _f_alvo_raw  = st.text_input("Valor alvo (R$) *", placeholder="Ex: 20.000,00")
                _f_atual_raw = st.text_input("Ja acumulado (R$)", value="0")
            with _fc3:
                _f_icone = st.selectbox("Icone", ICONES_META)
                _f_cor   = st.color_picker("Cor", value="#30D158")
            _fd1, _fd2, _fd3, _fd4 = st.columns(4)
            with _fd1:
                _f_ano = st.number_input("Prazo - Ano (0=sem)",
                                         min_value=0, max_value=2100, value=ANO_NOW)
            with _fd2:
                _f_mes = st.selectbox("Prazo - Mes",
                    options=list(range(0, 13)),
                    format_func=lambda x: _MESES_PT.get(x, ""),
                    index=MES_NOW)
            with _fd3:
                _submitted = st.form_submit_button("✅ Criar", width='stretch')
            with _fd4:
                _cancelled = st.form_submit_button("Cancelar", width='stretch')

            if _cancelled:
                st.session_state["show_form_meta"] = False
                st.rerun()
            if _submitted:
                _erros = []
                if not _f_nome.strip():
                    _erros.append("Nome e obrigatorio.")
                try:
                    _alvo_n = _parse_brl(_f_alvo_raw)
                    if _alvo_n <= 0:
                        _erros.append("Valor alvo deve ser maior que zero.")
                except ValueError as _ve:
                    _erros.append(str(_ve))
                    _alvo_n = 0.0
                try:
                    _atual_n = _parse_brl(_f_atual_raw) if _f_atual_raw.strip() else 0.0
                except ValueError:
                    _atual_n = 0.0
                if _erros:
                    for _e in _erros:
                        st.error(_e)
                else:
                    _ok, _err = add_meta(
                        username, _f_nome.strip(), _f_tipo,
                        _alvo_n, _atual_n, int(_f_ano), int(_f_mes), _f_cor, _f_icone,
                    )
                    if _ok:
                        st.success("Meta criada!")
                        st.session_state["show_form_meta"] = False
                        st.rerun()
                    else:
                        st.error(f"Erro: {_err}")
        st.divider()

    # ── KPIs ──────────────────────────────────────────────────────────────
    _df_todas = pd.concat([df_em_prog, df_concl], ignore_index=True) if not df.empty else pd.DataFrame()
    if not _df_todas.empty:
        _tot_alvo  = float(_df_todas["valor_alvo"].astype(float).sum())
        _tot_atual = float(_df_todas["valor_atual"].astype(float).sum())
        _pct_geral = (_tot_atual / _tot_alvo * 100) if _tot_alvo > 0 else 0.0
        _n_concl   = len(df_concl)
        _n_total   = len(_df_todas)
        _falta_tot = max(_tot_alvo - _tot_atual, 0.0)
        st.markdown(
            f"<div class='meta-kpi-grid'>"
            f"<div class='meta-kpi'><div class='meta-kpi-lbl'>💰 Total acumulado</div>"
            f"<div class='meta-kpi-val'>{brl(_tot_atual)}</div>"
            f"<div class='meta-kpi-sub'>de {brl(_tot_alvo)}</div></div>"
            f"<div class='meta-kpi'><div class='meta-kpi-lbl'>✅ Concluidas</div>"
            f"<div class='meta-kpi-val' style='color:#30D158'>{_n_concl} / {_n_total}</div>"
            f"<div class='meta-kpi-sub'>{_n_total - _n_concl} em progresso</div></div>"
            f"<div class='meta-kpi'><div class='meta-kpi-lbl'>📈 Progresso geral</div>"
            f"<div class='meta-kpi-val'>{_pct_geral:.1f}%</div>"
            f"<div class='meta-kpi-sub'>sobre todas as metas</div></div>"
            f"<div class='meta-kpi'><div class='meta-kpi-lbl'>💸 Ainda falta</div>"
            f"<div class='meta-kpi-val' style='color:#FF453A'>{brl(_falta_tot)}</div>"
            f"<div class='meta-kpi-sub'>para atingir tudo</div></div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # ── Metas em progresso ────────────────────────────────────────────────
    st.markdown("<div class='section-label'>METAS ATIVAS</div>", unsafe_allow_html=True)
    if df_em_prog.empty:
        st.markdown(
            "<div style='background:#1C1C1E;border:0.5px solid rgba(255,255,255,0.08);"
            "border-radius:16px;padding:32px;text-align:center;color:rgba(235,235,245,0.3)'>"
            "<div style='font-size:2rem;margin-bottom:8px'>🎯</div>"
            "<div>Nenhuma meta ativa. Clique em <b style='color:#FFF'>＋ Nova Meta</b>.</div>"
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        _nc = min(len(df_em_prog), 3)
        _cls = st.columns(_nc, gap="medium")
        for _i, (_, _r) in enumerate(df_em_prog.iterrows()):
            with _cls[_i % _nc]:
                st.markdown(_card_html(_r, concluida=False), unsafe_allow_html=True)
                st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
                _render_expander_meta(_r, username, brl)

    # ── Metas concluidas ──────────────────────────────────────────────────
    if not df_concl.empty:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<div class='section-label' style='color:#30D158'>✅ METAS CONCLUIDAS</div>",
            unsafe_allow_html=True,
        )
        _nc2 = min(len(df_concl), 3)
        _cls2 = st.columns(_nc2, gap="medium")
        for _i, (_, _r) in enumerate(df_concl.iterrows()):
            with _cls2[_i % _nc2]:
                st.markdown(_card_html(_r, concluida=True), unsafe_allow_html=True)
                st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
                # Expander simplificado para concluidas (so editar/excluir/reativar)
                with st.expander("✏️ Gerenciar"):
                    _rid  = str(_r["id"])
                    _ed_c = _ss_counter(f"ed_{_rid}")
                    _gb1, _gb2 = st.columns(2)
                    with _gb1:
                        if st.button("Reativar", key=f"reativ_{_rid}",
                                     width='stretch'):
                            _ok, _err = update_meta(
                                int(_r["id"]), username,
                                str(_r["nome"]), str(_r["tipo"]),
                                float(_r["valor_alvo"]), float(_r["valor_atual"]),
                                int(_r["prazo_ano"]), int(_r["prazo_mes"]),
                                str(_r["cor"]), str(_r["icone"]), True,
                            )
                            if _ok:
                                st.rerun()
                            else:
                                st.error(f"Erro: {_err}")
                    with _gb2:
                        if st.button("🗑 Excluir", key=f"del_c_{_rid}",
                                     width='stretch', type="primary"):
                            _ok, _err = delete_meta(int(_r["id"]))
                            if _ok:
                                st.rerun()
                            else:
                                st.error(f"Erro: {_err}")

    # ── Grafico Meta vs Realizado ─────────────────────────────────────────
    if not _df_todas.empty:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<div class='section-label'>META vs REALIZADO</div>", unsafe_allow_html=True
        )
        _df_chart = _df_todas.copy()
        _df_chart["valor_atual"] = _df_chart["valor_atual"].astype(float)
        _df_chart["valor_alvo"]  = _df_chart["valor_alvo"].astype(float)
        _df_chart["falta"]       = (_df_chart["valor_alvo"] - _df_chart["valor_atual"]).clip(lower=0)
        _df_chart["pct"]         = _df_chart.apply(_pct_meta, axis=1)
        _df_chart["label"]       = _df_chart.apply(
            lambda r: f"{r['icone']} {r['nome']}", axis=1
        )
        _df_chart = _df_chart.sort_values("pct", ascending=True)

        _fig = go.Figure()

        # Barra de alvo (fundo)
        _fig.add_trace(go.Bar(
            name="Meta (alvo)",
            y=_df_chart["label"].tolist(),
            x=_df_chart["valor_alvo"].tolist(),
            orientation="h",
            marker=dict(color="rgba(142,142,147,0.18)", line=dict(width=0)),
            hovertemplate="%{y}<br>Alvo: R$ %{x:,.2f}<extra></extra>",
        ))

        # Barra de realizado (frente) — cor por meta
        for _, _r in _df_chart.iterrows():
            _cor = str(_r["cor"]) if _r["cor"] else "#30D158"
            _fig.add_trace(go.Bar(
                name=str(_r["label"]),
                y=[_r["label"]],
                x=[float(_r["valor_atual"])],
                orientation="h",
                marker=dict(color=_cor, line=dict(width=0)),
                showlegend=False,
                hovertemplate=(
                    f"%{{y}}<br>"
                    f"Realizado: R$ %{{x:,.2f}}<br>"
                    f"Meta: {brl(float(_r['valor_alvo']))}<br>"
                    f"Progresso: {float(_r['pct']):.1f}%"
                    f"<extra></extra>"
                ),
            ))

        # Anotacoes de % no lado direito
        _max_alvo = float(_df_chart["valor_alvo"].max())
        for _, _r in _df_chart.iterrows():
            _fig.add_annotation(
                x=_max_alvo * 1.02,
                y=str(_r["label"]),
                text=f"<b>{float(_r['pct']):.0f}%</b>",
                showarrow=False,
                xanchor="left",
                font=dict(size=11, color="rgba(235,235,245,0.7)"),
            )

        _h_chart = max(120 + len(_df_chart) * 52, 280)
        _fig.update_layout(
            barmode="overlay",
            bargap=0.3,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="rgba(235,235,245,0.7)", size=12),
            margin=dict(l=8, r=80, t=16, b=8),
            height=_h_chart,
            legend=dict(
                orientation="h", yanchor="top", y=-0.08,
                xanchor="left", x=0,
                font=dict(size=11), bgcolor="rgba(0,0,0,0)",
            ),
            xaxis=dict(
                tickprefix="R$ ",
                gridcolor="rgba(161,161,170,.07)",
                zeroline=False,
                range=[0, _max_alvo * 1.16],
            ),
            yaxis=dict(showgrid=False),
        )
        st.plotly_chart(_fig, width='stretch', config={"displayModeBar": False})

    # ── Metas arquivadas manualmente ─────────────────────────────────────
    if not df_arq.empty:
        with st.expander(f"📦 Metas arquivadas ({len(df_arq)})"):
            for _, _r in df_arq.iterrows():
                _p    = _pct_meta(_r)
                _a1, _a2, _a3 = st.columns([5, 1.2, 1.2])
                with _a1:
                    st.markdown(
                        f"<div class='arq-row'>"
                        f"<div class='arq-info'><b>{_r['icone']} {_r['nome']}</b>"
                        f" <span style='opacity:.5;font-size:.8rem'>— {_r['tipo']}</span></div>"
                        f"<div class='arq-val'>"
                        f"{brl(float(_r['valor_atual']))} / {brl(float(_r['valor_alvo']))} · {_p:.0f}%"
                        f"</div></div>",
                        unsafe_allow_html=True,
                    )
                with _a2:
                    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                    if st.button("Reativar", key=f"reativ_arq_{_r['id']}",
                                 width='stretch'):
                        _ok, _err = update_meta(
                            int(_r["id"]), username,
                            str(_r["nome"]), str(_r["tipo"]),
                            float(_r["valor_alvo"]), float(_r["valor_atual"]),
                            int(_r["prazo_ano"]), int(_r["prazo_mes"]),
                            str(_r["cor"]), str(_r["icone"]), True,
                        )
                        if _ok:
                            st.rerun()
                        else:
                            st.error(f"Erro: {_err}")
                with _a3:
                    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                    if st.button("🗑 Excluir", key=f"del_arq_{_r['id']}",
                                 width='stretch', type="primary"):
                        _ok, _err = delete_meta(int(_r["id"]))
                        if _ok:
                            st.rerun()
                        else:
                            st.error(f"Erro: {_err}")
