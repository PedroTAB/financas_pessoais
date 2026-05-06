"""views/relatorio.py - Tela de Relatórios em PDF."""
import streamlit as st
import pandas as pd
from datetime import datetime

from utils.pdf_report import gerar_pdf
from data.storage import (
    get_lancamentos, get_ganhos, get_cartao_compras, get_parcelas_mes,
    MESES_ABR,
)

# Importar categorias do config (adapte conforme seu arquivo)
try:
    from config import CATEGORIAS_NECESSIDADES, CATEGORIAS_DESEJOS
except ImportError:
    CATEGORIAS_NECESSIDADES = [
        "Moradia", "Aluguel", "Condomínio", "Água", "Luz", "Gás",
        "Internet", "Telefone", "Supermercado", "Alimentação",
        "Transporte", "Combustível", "Saúde", "Médico", "Remédio",
        "Educação", "Faculdade", "Escola",
    ]
    CATEGORIAS_DESEJOS = [
        "Lazer", "Restaurante", "Streaming", "Assinatura",
        "Vestuário", "Roupas", "Academia", "Viagem",
        "Eletrônicos", "Presentes", "Beleza", "Pets",
    ]

MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}

_ESTILOS = """<style>
.rel-header{margin-bottom:4px}
.rel-card{background:#1C1C1E;border:0.5px solid rgba(255,255,255,0.08);
    border-radius:16px;padding:20px 22px}
.rel-section{font-size:.72rem;font-weight:700;letter-spacing:.1em;
    text-transform:uppercase;color:rgba(235,235,245,0.3);margin-bottom:10px}
.rel-kpi{display:flex;justify-content:space-between;align-items:center;
    padding:10px 0;border-bottom:0.5px solid rgba(255,255,255,0.06)}
.rel-kpi:last-child{border-bottom:none}
.rel-kpi-lbl{font-size:.82rem;color:rgba(235,235,245,0.6)}
.rel-kpi-val{font-size:.95rem;font-weight:700}
</style>"""


def show_relatorio(username: str):
    _now = datetime.now()
    st.markdown(_ESTILOS, unsafe_allow_html=True)

    # ── Header ────────────────────────────────────────────────────────────
    st.markdown(
        "<div style='font-size:1.5rem;font-weight:800;color:#FFFFFF;"
        "letter-spacing:-.02em;margin-bottom:4px'>📄 Relatórios</div>"
        "<div style='font-size:.82rem;color:rgba(235,235,245,0.3);margin-bottom:20px'>"
        "Gere relatórios financeiros detalhados em PDF</div>",
        unsafe_allow_html=True,
    )

    # ── Seleção de período ────────────────────────────────────────────────
    _sc1, _sc2, _sc3 = st.columns([1, 1, 2])
    with _sc1:
        _ano_sel = st.number_input("Ano", min_value=2020, max_value=2100,
                                   value=_now.year, step=1, key="rel_ano")
    with _sc2:
        _mes_sel = st.selectbox(
            "Mês", options=list(range(1, 13)),
            format_func=lambda x: MESES_PT.get(x, ""),
            index=_now.month - 1, key="rel_mes",
        )
    with _sc3:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        _btn_prev = st.button("🔍 Pré-visualizar dados", width='stretch',
                              key="btn_preview")

    _ano_sel = int(_ano_sel)
    _mes_sel = int(_mes_sel)
    _mes_label = MESES_PT.get(_mes_sel, "")

    # ── Preview ───────────────────────────────────────────────────────────
    if _btn_prev or st.session_state.get("rel_preview_loaded", False):
        st.session_state["rel_preview_loaded"] = True

        with st.spinner("Carregando dados..."):
            _df_lanc_mes  = get_lancamentos(username, ano=_ano_sel, mes=_mes_sel)
            _df_ganho_mes = get_ganhos(username, ano=_ano_sel, mes=_mes_sel)
            _df_cartao    = get_cartao_compras(username)
            _df_parc      = get_parcelas_mes(_df_cartao, _ano_sel, _mes_sel)
            _df_lanc_ano  = get_lancamentos(username, ano=_ano_sel)
            _df_ganho_ano = get_ganhos(username, ano=_ano_sel)

        # Cálculos rápidos para preview
        _tot_desp = 0.0
        _tot_rec_lanc = 0.0
        if not _df_lanc_mes.empty:
            _tot_desp = float(
                _df_lanc_mes[_df_lanc_mes["tipo"] == "Débito"]["valor"].astype(float).sum()
            )
            _tot_rec_lanc = float(
                _df_lanc_mes[_df_lanc_mes["tipo"] == "Crédito"]["valor"].astype(float).sum()
            )
        _tot_ganho = float(_df_ganho_mes["valor_liquido"].astype(float).sum()) if not _df_ganho_mes.empty else 0.0
        _tot_cartao = float(_df_parc["valor_parcela"].astype(float).sum()) if not _df_parc.empty else 0.0
        _tot_rec = _tot_rec_lanc + _tot_ganho
        _saldo = _tot_rec - _tot_desp - _tot_cartao

        def _brl(v):
            try:
                vf = float(v)
                s = f"R$ {abs(vf):,.2f}".replace(",","X").replace(".",",").replace("X",".")
                return f"-{s}" if vf < 0 else s
            except:
                return "R$ 0,00"

        def _cor(v, inv=False):
            ok = v >= 0 if not inv else v <= 0
            return "#30D158" if ok else "#FF453A"

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='rel-section'>Resumo — {_mes_label} {_ano_sel}</div>",
            unsafe_allow_html=True,
        )

        _kc1, _kc2, _kc3, _kc4 = st.columns(4)
        for _col, _lbl, _val, _cor in [
            (_kc1, "Receitas",  _brl(_tot_rec),   "#30D158"),
            (_kc2, "Despesas",  _brl(_tot_desp),  "#FF453A"),
            (_kc3, "Cartão",    _brl(_tot_cartao),"#FF9F0A"),
            (_kc4, "Saldo",     _brl(_saldo),     _cor(_saldo)),
        ]:
            _col.markdown(
                f"<div class='rel-card' style='text-align:center'>"
                f"<div class='rel-section'>{_lbl}</div>"
                f"<div style='font-size:1.1rem;font-weight:800;color:{_cor}'>{_val}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        # Contagem de registros
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        _info_parts = [
            f"**{len(_df_lanc_mes)}** lançamentos",
            f"**{len(_df_ganho_mes)}** ganhos",
        ]
        if not _df_parc.empty:
            _info_parts.append(f"**{len(_df_parc)}** parcelas de cartão")
        st.caption("Dados encontrados: " + " · ".join(_info_parts))

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Botão de geração do PDF ───────────────────────────────────────
        st.markdown(
            "<div class='rel-section'>Gerar Relatório</div>", unsafe_allow_html=True
        )
        _pc1, _pc2 = st.columns([2, 1])
        with _pc1:
            st.markdown(
                "<div style='font-size:.85rem;color:rgba(235,235,245,0.5)'>"
                "O PDF contém: Resumo do Mês, Gastos por Categoria, "
                "Regra 50/30/20, Cartão e Evolução Anual."
                "</div>",
                unsafe_allow_html=True,
            )
        with _pc2:
            if st.button("📄 Gerar PDF", width='stretch',
                         key="btn_gerar_pdf", type="primary"):
                with st.spinner("Gerando relatório..."):
                    try:
                        _pdf_bytes = gerar_pdf(
                            username=username,
                            ano=_ano_sel,
                            mes=_mes_sel,
                            df_lanc=_df_lanc_mes,
                            df_ganho=_df_ganho_mes,
                            df_cartao_parcelas=_df_parc,
                            df_lanc_ano=_df_lanc_ano,
                            df_ganho_ano=_df_ganho_ano,
                            cats_necessidades=CATEGORIAS_NECESSIDADES,
                            cats_desejos=CATEGORIAS_DESEJOS,
                        )
                        st.session_state["_pdf_bytes"]  = _pdf_bytes
                        st.session_state["_pdf_label"]  = f"{_mes_label}_{_ano_sel}"
                    except Exception as _e:
                        st.error(f"Erro ao gerar PDF: {_e}")

        # Botão de download (aparece após gerar)
        if st.session_state.get("_pdf_bytes"):
            _label = st.session_state.get("_pdf_label", "relatorio")
            st.download_button(
                label="⬇️ Baixar PDF",
                data=st.session_state["_pdf_bytes"],
                file_name=f"relatorio_{_label}.pdf",
                mime="application/pdf",
                width='stretch',
                key="btn_download_pdf",
            )
            st.success("PDF pronto! Clique em **Baixar PDF** para salvar.")
    else:
        # Estado inicial — instrução
        st.markdown(
            "<div style='background:#1C1C1E;border:0.5px solid rgba(255,255,255,0.08);"
            "border-radius:16px;padding:48px;text-align:center;color:rgba(235,235,245,0.3)'>"
            "<div style='font-size:2.5rem;margin-bottom:12px'>📄</div>"
            "<div style='font-size:.95rem;margin-bottom:6px;color:rgba(235,235,245,0.6)'>"
            "Selecione o período acima e clique em "
            "<b style='color:#FFFFFF'>Pré-visualizar dados</b></div>"
            "<div style='font-size:.8rem'>O relatório PDF será gerado com os dados do período escolhido.</div>"
            "</div>",
            unsafe_allow_html=True,
        )
