"""views/importar.py — v9: auto-categorização, histórico expandível, sem badges."""

from __future__ import annotations
import functools as _ft
import pandas as pd
import streamlit as st
from datetime import datetime

import data.storage as _st
from data.storage import _cached_records, CATEGORIAS_DEBITO, CATEGORIAS_CREDITO
from importers.ofx_importer import parse_ofx
from importers.csv_importer import parse_csv, BANCOS_SUPORTADOS
from utils.helpers import brl

FORMAS   = ["Dinheiro","Débito","Crédito","Pix","TED","DOC","Outros"]

# ── Auto-categorização por palavras-chave ──────────────────────────────────
_AUTO_CAT_DEBITO: list[tuple[list[str], str]] = [
    # Streaming
    (["netflix"], "Streaming"),
    (["spotify"], "Streaming"),
    (["disney", "star+", "starplus", "star plus"], "Streaming"),
    (["youtube premium", "youtube music", "youtube tv"], "Streaming"),
    (["hbo max", "hbo ", "max.com"], "Streaming"),
    (["globoplay", "globo play"], "Streaming"),
    (["paramount"], "Streaming"),
    (["deezer"], "Streaming"),
    (["twitch"], "Streaming"),
    (["prime video", "amazon video"], "Streaming"),
    # Assinaturas (software, cloud, apps)
    (["apple.com", "apple music", "apple tv", "apple one",
      "apple arcade", "apple news", "app store", "icloud"], "Assinaturas"),
    (["amazon prime", "amazon subscription",
      "amazon kindle", "amazon aws"], "Assinaturas"),
    (["google one", "google drive", "google storage",
      "google workspace"], "Assinaturas"),
    (["microsoft 365", "office 365", "onedrive",
      "xbox game pass", "xbox "], "Assinaturas"),
    (["chatgpt", "openai"], "Assinaturas"),
    (["adobe", "creative cloud"], "Assinaturas"),
    (["canva", "dropbox", "notion", "github",
      "duolingo", "linkedin premium"], "Assinaturas"),
    (["mercado play", "meli+", "mercadoplay"], "Assinaturas"),
    # Restaurantes (delivery e comida fora)
    (["ifood", "i food", "rappi", "uber eats", "ubereats",
      "james delivery", "aiqfome", "99food"], "Restaurantes"),
    (["mcdonalds", "mcdonald", "burger king", "subway", "kfc",
      "bob's", "giraffas", "outback", "pizza hut", "dominos",
      "habib", "madero", "china in box"], "Restaurantes"),
    (["padaria", "lanchonete", "restaurante", "sushi",
      "churrascaria", "cafeteria", "cafe "], "Restaurantes"),
    # Subsistência (mercados)
    (["supermercado", "hipermercado", "carrefour", "pao de acucar",
      "extra ", "atacadao", "assai ", "sams club",
      "hortifruti", "mercadinho"], "Subsistência"),
    # Transporte
    (["uber ", "99pop", "99taxi", "99 taxi", "cabify", "taxi "], "Transporte"),
    (["posto gasolina", "shell ", "ipiranga ",
      "petrobras ", "combustivel"], "Transporte"),
    (["metro ", "metrosp", "cptm", "onibus ",
      "bilhete unico", "sptrans"], "Transporte"),
    # Saúde
    (["farmacia", "drogaria", "droga", "ultrafarma",
      "drogasil", "pacheco", "raia ", "nissei"], "Saúde"),
    (["hospital", "clinica", "laboratorio", "consulta ",
      "dentista", "odonto", "fisioterapia",
      "plano de saude", "unimed", "amil"], "Saúde"),
    # Lazer
    (["cinema", "cinesystem", "cinemark", "uci ",
      "ingresso.com", "ingresso "], "Lazer"),
    (["steam", "playstation", "nintendo", "epic games", "nuuvem"], "Lazer"),
    (["show ", "teatro ", "eventbrite", "sympla"], "Lazer"),
    # Educação
    (["udemy", "coursera", "alura", "rocketseat",
      "pluralsight", "skillshare", "domestika"], "Educação"),
    (["escola ", "faculdade", "universidade", "mensalidade "], "Educação"),
    # Conta (utilities)
    (["enel ", "elektro", "cemig", "cpfl ", "light ",
      "coelba", "energisa", "copel "], "Conta"),
    (["sabesp", "cedae", "sanepar", "embasa", "cagece", "copasa"], "Conta"),
    (["vivo ", "claro ", "tim ", "oi ",
      "net ", "sky ", "nextel", "internet "], "Conta"),
    (["pagamento boleto", "boleto bancario"], "Conta"),
    # Eletrônicos
    (["kabum", "terabyte", "pichau"], "Eletrônicos"),
    # Moradia
    (["aluguel", "condominio", "condomínio",
      "iptu", "seguro residencial"], "Moradia"),
    # Viagem
    (["booking", "airbnb", "trivago",
      "latam", "gol ", "azul ", "tam "], "Viagem"),
    # Pets
    (["pet shop", "petshop", "cobasi",
      "petz", "veterinari", "vet "], "Pets"),
]

_AUTO_CAT_CREDITO: list[tuple[list[str], str]] = [
    (["estorno", "reembolso", "devolucao", "devolução",
      "ressarcimento", "chargeback"], "Estorno"),
    (["restituicao", "restituição", "receita federal",
      "imposto de renda restituido"], "Restituição"),
    (["acordo", "negociacao", "negociação",
      "renegociacao", "renegociação"], "Acordo"),
    (["venda", "recebimento venda", "deposito venda"], "Venda"),
    (["cashback", "premio ", "prêmio",
      "bonificacao", "bonificação", "premiacao"], "Premiação"),
]


def _auto_cat(descricao: str, cat_atual, tipo: str,
              cats_debito: list, cats_credito: list) -> str:
    """Sugere categoria por palavras-chave. Respeita categoria já preenchida."""
    import math
    # Normaliza NaN / None / "" → sem categoria
    _c = ""
    if cat_atual is not None:
        try:
            if isinstance(cat_atual, float) and math.isnan(cat_atual):
                _c = ""
            else:
                _c = str(cat_atual).strip()
        except Exception:
            _c = ""
    _sem = {"", "nan", "none", "outros", "sem categoria",
            "other", "uncategorized", "-", "—"}
    if _c.lower() not in _sem:
        return _c  # já tem categoria válida

    desc_low = str(descricao).lower().strip()
    is_cred  = str(tipo).strip().lower() in [
        "crédito", "credito", "credit", "entrada"]

    if is_cred:
        for kws, cat in _AUTO_CAT_CREDITO:
            if any(kw in desc_low for kw in kws):
                return cat if cat in cats_credito else "Outros"
        return "Outros"
    else:
        for kws, cat in _AUTO_CAT_DEBITO:
            if any(kw in desc_low for kw in kws):
                return cat if cat in cats_debito else "Outros"
        return "Outros"


MESES_PT = {1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",
            7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}

_STEP_UPLOAD  = "upload"
_STEP_PREVIEW = "preview"
_STEP_DONE    = "done"

_CSS = """<style>
/* ─── título ─── */
.imp-title{font-size:1.5rem;font-weight:800;color:#FFF;letter-spacing:-.02em}
.imp-sub{font-size:.82rem;color:rgba(235,235,245,0.35);margin-top:3px;margin-bottom:20px}
.imp-title-badge-removed{display:inline-flex;align-items:center;font-size:.68rem;font-weight:700;
    letter-spacing:.08em;text-transform:uppercase;padding:3px 10px;border-radius:999px;
    background:rgba(10,132,255,0.12);color:#0A84FF;border:.5px solid rgba(10,132,255,0.25);
    margin-left:10px;vertical-align:middle}

/* ─── stat cards ─── */
.imp-stat{background:#2C2C2E;border-radius:14px;padding:14px 18px;
    position:relative;overflow:hidden}
.imp-stat-accent{position:absolute;top:0;left:0;right:0;height:2.5px;
    border-radius:14px 14px 0 0}
.imp-stat-val{font-size:1.4rem;font-weight:800;letter-spacing:-.03em;color:#FFF;
    font-feature-settings:"tnum";margin-top:4px}
.imp-stat-lbl{font-size:.68rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
    color:rgba(235,235,245,0.35)}
.imp-stat-sub{font-size:.72rem;color:rgba(235,235,245,0.3);margin-top:3px}

/* ─── section labels (sem box) ─── */
.imp-sec-lbl{font-size:.72rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
    color:rgba(235,235,245,0.38);margin:14px 0 8px}
.imp-sep{border-top:.5px solid rgba(255,255,255,0.07);margin:18px 0}

/* ─── cartão section (leve, só borda esquerda) ─── */
.imp-cartao-wrap{border-left:2px solid rgba(255,159,10,0.4);
    padding-left:14px;margin-bottom:14px}
.imp-cartao-lbl{font-size:.72rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
    color:rgba(255,159,10,.8);margin-bottom:10px}

/* ─── histórico ─── */
.imp-hist-lbl{font-size:.72rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
    color:rgba(235,235,245,0.38);margin:18px 0 10px}
.imp-hist-empty{background:#2C2C2E;border-radius:14px;padding:28px 20px;text-align:center;
    color:rgba(235,235,245,0.25);font-size:.88rem;margin-bottom:8px}

/* ─── tip ─── */
.imp-tip{background:rgba(10,132,255,0.06);border:.5px solid rgba(10,132,255,0.16);
    border-radius:10px;padding:9px 13px;font-size:.78rem;
    color:rgba(235,235,245,0.45);margin-top:10px}
.imp-warn{background:rgba(255,159,10,0.08);border:.5px solid rgba(255,159,10,0.18);
    border-radius:10px;padding:9px 13px;font-size:.78rem;
    color:rgba(255,159,10,.85);margin-bottom:10px}

/* ─── footer bar ─── */
.imp-footer{display:flex;gap:14px;align-items:center;padding:12px 16px;
    background:#2C2C2E;border-radius:12px;margin:8px 0;font-size:.84rem}

/* ─── success ─── */
.imp-success{background:rgba(48,209,88,0.07);border:.5px solid rgba(48,209,88,0.22);
    border-radius:14px;padding:18px 22px;font-size:1rem;color:#30D158;
    margin-bottom:16px;text-align:center;font-weight:600}
</style>"""

# ── helpers ──────────────────────────────────────────────────────────────────
def _safe_int(v, default=0):
    try:
        if v is None or (isinstance(v, float) and v != v): return default
        return int(float(str(v).strip()))
    except: return default

def _safe_float(v, default=0.0):
    try: return float(str(v).strip().replace(",", "."))
    except: return default

def _get_cartoes_cfg_safe(fn):
    try:
        c = fn()
        if c: return c
    except: pass
    try: return _st.get_cartoes_cfg() or []
    except: return []

def _max_id(fn):
    try:
        df = fn()
        return _safe_int(df["id"].max(), 0) if not df.empty else 0
    except: return 0

def _novos_registros(fn, max_antes):
    _cached_records.clear()
    try:
        df = fn()
        if df.empty: return pd.DataFrame()
        df["id"] = df["id"].apply(lambda x: _safe_int(x, 0))
        return df[df["id"] > max_antes].copy()
    except: return pd.DataFrame()

def _reset():
    """Limpa estado de upload — preserva imp_last_import."""
    for k in ["imp_df","imp_step","imp_filename","imp_banco",
              "imp_ok_cart","imp_ok_lanc","imp_erros"]:
        st.session_state.pop(k, None)

def _stat_card(col, val, lbl, sub="", color="#8E8E93"):
    col.markdown(
        f"<div class='imp-stat'>"
        f"<div class='imp-stat-accent' style='background:{color}'></div>"
        f"<div class='imp-stat-lbl'>{lbl}</div>"
        f"<div class='imp-stat-val' style='color:{color}'>{val}</div>"
        f"<div class='imp-stat-sub'>{sub}</div>"
        f"</div>", unsafe_allow_html=True)

def _fmt_hora(s):
    try: return datetime.strptime(str(s), "%Y-%m-%d %H:%M").strftime("%d/%m/%y %H:%M")
    except: return str(s)


# ══════════════════════════════════════════════════════════════════════════════
def show_importar(username: str):
    get_lancamentos      = _ft.partial(_st.get_lancamentos,      username)
    add_lancamento       = _ft.partial(_st.add_lancamento,       username)
    delete_lancamento    = _ft.partial(_st.delete_lancamento,    username)
    get_cartao_compras   = _ft.partial(_st.get_cartao_compras,   username)
    add_cartao_compra    = _ft.partial(_st.add_cartao_compra,    username)
    delete_cartao_compra = _ft.partial(_st.delete_cartao_compra, username)
    get_cartoes_cfg      = _ft.partial(_st.get_cartoes_cfg,      username)

    _has_log  = hasattr(_st, "get_import_log")  and hasattr(_st, "add_import_log")
    _has_txns    = hasattr(_st, "get_import_transactions")
    _has_upd_log = hasattr(_st, "update_import_log_counts")
    # Verifica se o patch v3 foi aplicado (add_import_log com 8 params)
    import inspect as _insp
    if _has_log:
        try:
            _n_params = len(_insp.signature(_st.add_import_log).parameters)
            if _n_params < 7:
                _has_log = False  # versão antiga do patch, ignorar
        except Exception:
            pass

    st.markdown(_CSS, unsafe_allow_html=True)
    step = st.session_state.get("imp_step", _STEP_UPLOAD)

    # ══════════════════════════════════════════════════════════════
    # STEP 1 — MAIN PAGE
    # ══════════════════════════════════════════════════════════════
    if step == _STEP_UPLOAD:
        st.markdown(
            "<div class=\'imp-title\'>📥 Importar Extrato</div>"
            "<div class=\'imp-sub\'>Carregue um extrato CSV ou OFX e revise antes de salvar</div>",
            unsafe_allow_html=True)

        # ── Stat cards ────────────────────────────────────────────
        df_log = _st.get_import_log(username) if _has_log else pd.DataFrame()

        total_imp  = len(df_log)
        total_lanc = int(df_log["n_lancamentos"].sum()) if not df_log.empty else 0
        total_cart = int(df_log["n_cartao"].sum())      if not df_log.empty else 0
        ultima     = _fmt_hora(df_log["data_hora"].iloc[0]) if not df_log.empty else "—"

        c1,c2,c3,c4 = st.columns(4)
        _stat_card(c1, str(total_imp),  "Importações",      "total de arquivos", "#0A84FF")
        _stat_card(c2, str(total_lanc), "Lançamentos",       "importados",         "#30D158")
        _stat_card(c3, str(total_cart), "Compras Cartão",    "importadas",         "#FF9F0A")
        _stat_card(c4, str(ultima),     "Última Importação", "data e hora",        "#8E8E93")

        # ── Separador + Upload (topo, sem box) ───────────────────
        st.markdown("<div class='imp-sep'></div>", unsafe_allow_html=True)
        st.markdown("<div class='imp-sec-lbl'>📂 Carregar novo extrato</div>",
                    unsafe_allow_html=True)

        col_tipo, col_banco = st.columns([1, 2])
        with col_tipo:
            tipo_arq = st.radio("Formato", ["OFX / OFC","CSV"],
                                horizontal=True, key="imp_tipo_arq")
        with col_banco:
            if tipo_arq == "CSV":
                banco_sel = st.selectbox("Banco",
                                         ["Auto-detectar"] + BANCOS_SUPORTADOS,
                                         key="imp_banco_sel")
            else:
                banco_sel = "OFX"
                st.caption("OFX / OFC é o padrão dos bancos brasileiros (Itaú, Bradesco, BB…)")

        ext = ["ofx","ofc"] if tipo_arq == "OFX / OFC" else ["csv","txt"]
        arquivo = st.file_uploader(f"Arquivo {tipo_arq}", type=ext, key="imp_file_uploader")

        st.markdown("""<div class='imp-tip'>
            💡 <b>Como exportar:</b>&nbsp;
            Nubank → App → Exportar CSV &nbsp;|&nbsp;
            Itaú / Bradesco → Internet Banking → OFX &nbsp;|&nbsp;
            Inter → App → Baixar CSV
        </div>""", unsafe_allow_html=True)

        if arquivo is not None:
            with st.spinner("Lendo arquivo…"):
                try:
                    hint = None if banco_sel in ("Auto-detectar","OFX") else banco_sel
                    df_p = (parse_ofx(arquivo.read()) if tipo_arq == "OFX / OFC"
                            else parse_csv(arquivo.read(), bank_hint=hint))

                    # Normalizar forma_pagamento (OFX não distingue cartão)
                    if "forma_pagamento" not in df_p.columns:
                        df_p["forma_pagamento"] = "Débito"
                    _cart_kw = [
                        "compra cartao", "compra cartão",
                        "debito cartao", "debito cartão",
                        "pgto cartao", "parcelado", "compra parcelada",
                        "credito cartao", "crédito cartão",
                    ]
                    def _fix_forma(r):
                        fp = str(r.get("forma_pagamento", "") or "").strip()
                        desc = str(r.get("descricao", "") or "").lower()
                        if fp == "Crédito":
                            return "Crédito"
                        if any(k in desc for k in _cart_kw):
                            return "Crédito"
                        return fp if fp else "Débito"
                    df_p["forma_pagamento"] = df_p.apply(_fix_forma, axis=1)

                    df_p["num_parcelas"] = 1
                    df_p["importar"]     = True
                    # Auto-categorizar (NaN-safe, separa débito/crédito)
                    df_p["categoria"] = df_p.apply(
                        lambda r: _auto_cat(
                            r.get("descricao", "") or "",
                            r.get("categoria", None),
                            r.get("tipo", "") or "",
                            CATEGORIAS_DEBITO,
                            CATEGORIAS_CREDITO,
                        ), axis=1
                    )
                    st.session_state.update({
                        "imp_df": df_p, "imp_step": _STEP_PREVIEW,
                        "imp_filename": arquivo.name, "imp_banco": banco_sel,
                    })
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")

        # ── Histórico de importações (abaixo do upload) ───────────
        st.markdown("<div class='imp-sep'></div>", unsafe_allow_html=True)
        st.markdown("<div class='imp-hist-lbl'>📋 Histórico de importações</div>",
                    unsafe_allow_html=True)

        if df_log.empty:
            st.markdown(
                "<div class='imp-hist-empty'>Nenhuma importação registrada ainda.<br>"
                "<span style='font-size:.75rem'>Carregue seu primeiro extrato acima ↑</span>"
                "</div>", unsafe_allow_html=True)
        else:
            # Filtros
            all_meses = []
            for m_str in df_log["meses"].dropna():
                for m in str(m_str).split(","):
                    m = m.strip()
                    if m and m not in all_meses: all_meses.append(m)

            hf1, hf2, _ = st.columns([2,2,3])
            with hf1:
                flt_mes = st.multiselect("", sorted(all_meses),
                                         placeholder="🗓 Filtrar por mês…",
                                         key="imp_hist_flt_mes",
                                         label_visibility="collapsed")
            with hf2:
                flt_arq = st.text_input("", placeholder="🔍 Buscar arquivo…",
                                        key="imp_hist_flt_arq",
                                        label_visibility="collapsed")

            df_show = df_log.copy()
            if flt_mes:
                df_show = df_show[df_show["meses"].apply(
                    lambda m: any(f in str(m) for f in flt_mes))]
            if flt_arq.strip():
                df_show = df_show[df_show["arquivo"].str.contains(
                    flt_arq.strip(), case=False, na=False)]

            if df_show.empty:
                st.caption("Nenhum resultado para o filtro.")
            else:
                # Cada linha do histórico é um expander expandível
                for _, row in df_show.iterrows():
                    log_id   = _safe_int(row.get("id", 0))
                    arq_nome = str(row.get("arquivo","—"))
                    hora     = _fmt_hora(row.get("data_hora",""))
                    n_l      = _safe_int(row.get("n_lancamentos", 0))
                    n_c      = _safe_int(row.get("n_cartao", 0))
                    meses    = str(row.get("meses",""))
                    banco    = str(row.get("banco","—"))
                    ids_l    = str(row.get("ids_lancamentos",""))
                    ids_c    = str(row.get("ids_cartao",""))

                    header = (f"{arq_nome}   {hora}"
                              f"   |   💳 {n_c}   📋 {n_l}"
                              f"   ·   {meses}")

                    with st.expander(header, expanded=False):
                        st.caption(f"Banco: {banco}")

                        # Buscar transações se temos os IDs e a função existe
                        tem_ids = bool((ids_l.strip() or ids_c.strip()) and _has_txns)
                        if not tem_ids:
                            st.info("⚠️ IDs não registrados — importação feita com versão anterior.")
                            _has_del_entry = hasattr(_st, "delete_import_log_entry")
                            if _has_del_entry:
                                if st.button("🗑️ Remover do histórico",
                                             key=f"del_entry_{log_id}",
                                             use_container_width=True):
                                    _st.delete_import_log_entry(log_id)
                                    st.rerun()
                        else:
                            # Cache por log_id para evitar chamadas repetidas ao Sheets
                            _cache_key = f"_imp_txn_{log_id}"
                            if _cache_key not in st.session_state:
                                with st.spinner("Carregando transações..."):
                                    try:
                                        _tl, _tc = _st.get_import_transactions(
                                            username, ids_l, ids_c)
                                        st.session_state[_cache_key] = (_tl, _tc)
                                    except Exception as _e:
                                        st.session_state[_cache_key] = (
                                            pd.DataFrame(), pd.DataFrame())
                            df_tl, df_tc = st.session_state[_cache_key]

                            # Garantir coluna "id" (pode faltar se get_cartao_compras
                            # não a retorna ou a importação foi feita antes).
                            # Nota: o guard anterior "if not df.empty" impedia que
                            # DataFrames vazios recebessem a coluna, causando KeyError
                            # ao tentar df_tc["id"] no botão "Excluir importação completa".
                            if "id" not in df_tl.columns:
                                df_tl["id"] = range(len(df_tl))
                            if "id" not in df_tc.columns:
                                df_tc["id"] = range(len(df_tc))

                            # ── Compras de cartão ─────────────────────────────
                            if not df_tc.empty:
                                st.markdown("**💳 Compras no Cartão**")
                                ed_c_key = f"rb_cart_{log_id}"
                                if ed_c_key not in st.session_state:
                                    st.session_state[ed_c_key] = False

                                df_tc_d = df_tc[["id","descricao","valor_total",
                                                  "num_parcelas","cartao"]].copy()
                                df_tc_d.insert(0, "excluir", False)
                                df_tc_d = df_tc_d.rename(columns={
                                    "descricao":"Descrição","valor_total":"R$",
                                    "num_parcelas":"Parcelas","cartao":"Cartão"})

                                ed_c = st.data_editor(
                                    df_tc_d[["excluir","Descrição","R$","Parcelas","Cartão"]],
                                    column_config={
                                        "excluir":   st.column_config.CheckboxColumn("🗑️", width="small"),
                                        "Descrição": st.column_config.TextColumn(disabled=True, width="large"),
                                        "R$":        st.column_config.NumberColumn(format="R$ %.2f", disabled=True, width="small"),
                                        "Parcelas":  st.column_config.NumberColumn(disabled=True, width="small"),
                                        "Cartão":    st.column_config.TextColumn(disabled=True, width="small"),
                                    },
                                    hide_index=True, use_container_width=True,
                                    key=f"ed_c_{log_id}")

                                if ed_c is not None:
                                    df_tc_d["excluir"] = ed_c["excluir"].values

                                n_sel_c = int(df_tc_d["excluir"].sum())
                                bc1, bc2 = st.columns([1,1])
                                with bc1:
                                    if st.button(f"🗑️ Excluir {n_sel_c} selecionada(s)",
                                                 disabled=n_sel_c==0,
                                                 key=f"del_c_sel_{log_id}",
                                                 use_container_width=True):
                                        excl = 0
                                        # data_editor retorna o nome original da coluna ("excluir"),
                                        # não o label de exibição ("🗑️") definido no column_config.
                                        ids_sel = df_tc.loc[df_tc_d[df_tc_d["excluir"]].index, "id"].tolist() if ed_c is not None else []
                                        for xid in ids_sel:
                                            ok, _ = delete_cartao_compra(_safe_int(xid))
                                            if ok:
                                                excl += 1
                                        _cached_records.clear()
                                        st.session_state.pop(f"_imp_txn_{log_id}", None)
                                        if _has_upd_log or hasattr(_st, "delete_import_log_entry"):
                                            try:
                                                _rl, _rc = _st.get_import_transactions(username, ids_l, ids_c)
                                                _n_rl, _n_rc = len(_rl), len(_rc)
                                                if _n_rl == 0 and _n_rc == 0 and hasattr(_st, "delete_import_log_entry"):
                                                    _st.delete_import_log_entry(log_id)
                                                elif _has_upd_log:
                                                    _st.update_import_log_counts(log_id, _n_rl, _n_rc)
                                            except Exception:
                                                pass
                                        st.success(f"✅ {excl} compra(s) removida(s).")
                                        st.rerun()
                                with bc2:
                                    if st.button(f"🗑️ Excluir todas as {len(df_tc)} compras",
                                                 key=f"del_c_all_{log_id}",
                                                 use_container_width=True):
                                        excl = 0
                                        for xid in df_tc["id"].tolist():
                                            ok, _ = delete_cartao_compra(_safe_int(xid))
                                            if ok:
                                                excl += 1
                                        _cached_records.clear()
                                        st.session_state.pop(f"_imp_txn_{log_id}", None)
                                        if _has_upd_log or hasattr(_st, "delete_import_log_entry"):
                                            try:
                                                _rl, _rc = _st.get_import_transactions(username, ids_l, ids_c)
                                                _n_rl, _n_rc = len(_rl), len(_rc)
                                                if _n_rl == 0 and _n_rc == 0 and hasattr(_st, "delete_import_log_entry"):
                                                    _st.delete_import_log_entry(log_id)
                                                elif _has_upd_log:
                                                    _st.update_import_log_counts(log_id, _n_rl, _n_rc)
                                            except Exception:
                                                pass
                                        st.success(f"✅ {excl} compra(s) removida(s).")
                                        st.rerun()

                            # ── Lançamentos ───────────────────────────────────
                            if not df_tl.empty:
                                st.markdown("**📋 Lançamentos**")
                                df_tl_d = df_tl[["id","descricao","valor","tipo","categoria"]].copy()
                                df_tl_d.insert(0, "excluir", False)
                                df_tl_d = df_tl_d.rename(columns={
                                    "descricao":"Descrição","valor":"R$",
                                    "tipo":"Tipo","categoria":"Categoria"})

                                ed_l = st.data_editor(
                                    df_tl_d[["excluir","Descrição","R$","Tipo","Categoria"]],
                                    column_config={
                                        "excluir":   st.column_config.CheckboxColumn("🗑️", width="small"),
                                        "Descrição": st.column_config.TextColumn(disabled=True, width="large"),
                                        "R$":        st.column_config.NumberColumn(format="R$ %.2f", disabled=True, width="small"),
                                        "Tipo":      st.column_config.TextColumn(disabled=True, width="small"),
                                        "Categoria": st.column_config.TextColumn(disabled=True, width="medium"),
                                    },
                                    hide_index=True, use_container_width=True,
                                    key=f"ed_l_{log_id}")

                                if ed_l is not None:
                                    df_tl_d["excluir"] = ed_l["excluir"].values

                                n_sel_l = int(df_tl_d["excluir"].sum())
                                bl1, bl2 = st.columns([1,1])
                                with bl1:
                                    if st.button(f"🗑️ Excluir {n_sel_l} selecionado(s)",
                                                 disabled=n_sel_l==0,
                                                 key=f"del_l_sel_{log_id}",
                                                 use_container_width=True):
                                        excl = 0
                                        # data_editor retorna o nome original da coluna ("excluir"),
                                        # não o label de exibição ("🗑️") definido no column_config.
                                        ids_sel = df_tl.loc[df_tl_d[df_tl_d["excluir"]].index, "id"].tolist() if ed_l is not None else []
                                        for xid in ids_sel:
                                            ok, _ = delete_lancamento(_safe_int(xid))
                                            if ok:
                                                excl += 1
                                        _cached_records.clear()
                                        st.session_state.pop(f"_imp_txn_{log_id}", None)
                                        if _has_upd_log or hasattr(_st, "delete_import_log_entry"):
                                            try:
                                                _rl, _rc = _st.get_import_transactions(username, ids_l, ids_c)
                                                _n_rl, _n_rc = len(_rl), len(_rc)
                                                if _n_rl == 0 and _n_rc == 0 and hasattr(_st, "delete_import_log_entry"):
                                                    _st.delete_import_log_entry(log_id)
                                                elif _has_upd_log:
                                                    _st.update_import_log_counts(log_id, _n_rl, _n_rc)
                                            except Exception:
                                                pass
                                        st.success(f"✅ {excl} lançamento(s) removido(s).")
                                        st.rerun()
                                with bl2:
                                    if st.button(f"🗑️ Excluir todos os {len(df_tl)} lançamentos",
                                                 key=f"del_l_all_{log_id}",
                                                 use_container_width=True):
                                        excl = 0
                                        for xid in df_tl["id"].tolist():
                                            ok, _ = delete_lancamento(_safe_int(xid))
                                            if ok:
                                                excl += 1
                                        _cached_records.clear()
                                        st.session_state.pop(f"_imp_txn_{log_id}", None)
                                        if _has_upd_log or hasattr(_st, "delete_import_log_entry"):
                                            try:
                                                _rl, _rc = _st.get_import_transactions(username, ids_l, ids_c)
                                                _n_rl, _n_rc = len(_rl), len(_rc)
                                                if _n_rl == 0 and _n_rc == 0 and hasattr(_st, "delete_import_log_entry"):
                                                    _st.delete_import_log_entry(log_id)
                                                elif _has_upd_log:
                                                    _st.update_import_log_counts(log_id, _n_rl, _n_rc)
                                            except Exception:
                                                pass
                                        st.success(f"✅ {excl} lançamento(s) removido(s).")
                                        st.rerun()


                            # ── Excluir importação completa (rodapé do expander) ──
                            st.markdown("""
                            <style>
                            div[data-testid="stButton"] button[kind="secondary"][id*="del_full_"] {
                                border-color: rgba(255,69,58,0.35) !important;
                                color: #FF453A !important;
                            }
                            </style>
                            """, unsafe_allow_html=True)
                            st.divider()
                            _has_del = hasattr(_st, "delete_import_log_entry")
                            _total_txn = len(df_tl) + len(df_tc)
                            _d1, _d2, _d3 = st.columns([2, 2, 1])
                            with _d2:
                                st.markdown(
                                    f"<div style='text-align:center;font-size:.75rem;"
                                    f"color:rgba(235,235,245,0.3);margin-bottom:4px'>"
                                    f"Esta ação remove todas as {_total_txn} transações desta importação</div>",
                                    unsafe_allow_html=True)
                                if st.button(
                                    "🗑️ Excluir importação completa",
                                    key=f"del_full_{log_id}",
                                    use_container_width=True,
                                    help="Remove TODAS as transações e apaga esta entrada do histórico",
                                ):
                                    _ok_full = 0
                                    for _xid in df_tc["id"].tolist():
                                        _ok, _ = delete_cartao_compra(_safe_int(_xid))
                                        if _ok: _ok_full += 1
                                    for _xid in df_tl["id"].tolist():
                                        _ok, _ = delete_lancamento(_safe_int(_xid))
                                        if _ok: _ok_full += 1
                                    _cached_records.clear()
                                    st.session_state.pop(f"_imp_txn_{log_id}", None)
                                    if _has_del:
                                        _st.delete_import_log_entry(log_id)
                                    elif _has_upd_log:
                                        try:
                                            _st.update_import_log_counts(log_id, 0, 0)
                                        except Exception:
                                            pass
                                    st.success(
                                        f"✅ Importação excluída — {_ok_full} transações removidas.")
                                    st.rerun()
    # ══════════════════════════════════════════════════════════════
    # STEP 2 — REVISÃO
    # ══════════════════════════════════════════════════════════════
    elif step == _STEP_PREVIEW:
        df: pd.DataFrame = st.session_state.get("imp_df", pd.DataFrame())
        if df.empty:
            st.warning("Nenhuma transação carregada.")
            if st.button("↩ Voltar"): _reset(); st.rerun()
            return

        if "data" in df.columns:
            df["_ano"] = pd.to_datetime(df["data"], errors="coerce").dt.year.fillna(0).astype(int)
            df["_mes"] = pd.to_datetime(df["data"], errors="coerce").dt.month.fillna(0).astype(int)
        else:
            df["_ano"] = df["ano"].apply(_safe_int)
            df["_mes"] = df["mes"].apply(_safe_int)

        # Ignorar pares com ano/mes inválidos (0,0) que vêm de datas mal parseadas
        pares  = sorted(set(
            (a, m) for a, m in zip(df["_ano"], df["_mes"])
            if a > 0 and m > 0
        ))
        labels = {(a,m): f"{MESES_PT.get(m,m)}/{str(a)[2:]}" for a,m in pares}

        # Sem filtro de mês — sempre mostrar todas as transações
        sel_pares = pares
        _hdr_col1, _hdr_col2 = st.columns([5, 1])
        with _hdr_col2:
            if st.button("↩ Cancelar"): _reset(); st.rerun()

        df_view = df[df.apply(
            lambda r: (_safe_int(r["_ano"]), _safe_int(r["_mes"])) in sel_pares, axis=1
        )].copy() if sel_pares else df.copy()

        cats        = sorted(set(CATEGORIAS_DEBITO + CATEGORIAS_CREDITO))
        mask_cartao = df_view["forma_pagamento"] == "Crédito"
        df_cartao   = df_view[mask_cartao].copy()
        df_outros   = df_view[~mask_cartao].copy()

        # métricas
        n_cart = len(df_cartao)
        m1,m2,m3,m4 = st.columns(4)
        _stat_card(m1, str(len(df_view)), "Transações",  "", "#8E8E93")
        _stat_card(m2, brl(df_view[df_view["tipo"]=="Crédito"]["valor"].sum()), "Entradas","","#30D158")
        _stat_card(m3, brl(df_view[df_view["tipo"]=="Débito"]["valor"].sum()),  "Saídas",  "","#FF453A")
        _stat_card(m4, str(n_cart), "No Cartão","","#FF9F0A")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        # ── Seção Cartão (borda esquerda leve) ───────────────────
        if not df_cartao.empty:
            st.markdown("<div class='imp-cartao-wrap'>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='imp-cartao-lbl'>💳 Compras no Cartão — {len(df_cartao)} transações</div>",
                unsafe_allow_html=True)

            cfgs = _get_cartoes_cfg_safe(get_cartoes_cfg)
            if not cfgs:
                st.markdown("<div class='imp-warn'>⚠️ Nenhum cartão cadastrado. "
                            "Vá em <b>Cartões</b> para cadastrar um. "
                            "Estas compras serão ignoradas.</div>", unsafe_allow_html=True)
                df.loc[df_cartao.index, "importar"] = False
            else:
                nomes = [f"{c['nome']} (…{c['digitos']})" for c in cfgs]
                cc1, cc2, cc3 = st.columns([3,1,1])
                with cc1:
                    idx = st.selectbox("Cartão:", nomes, key="imp_cartao_sel")
                    st.session_state["imp_cartao_nome"] = cfgs[nomes.index(idx)]["nome"]
                with cc2:
                    pg_default = st.number_input(
                        "Parcelas padrão", min_value=1, max_value=48,
                        value=1, step=1, key="imp_parc_default",
                        help="Valor padrão — clique em ↕ para aplicar a todas")
                with cc3:
                    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                    if st.button("↕ Aplicar a todas", key="btn_apply_parc",
                                 use_container_width=True):
                        df.loc[df_cartao.index, "num_parcelas"] = int(pg_default)
                        st.session_state["imp_df"] = df
                        st.rerun()

                st.caption("✏️ Edite **Parcelas** por linha para compras parceladas individualmente.")

                ca, cb, _ = st.columns([1,1,6])
                with ca:
                    if st.button("✅ Todas",   key="cart_all"):
                        df.loc[df_cartao.index,"importar"] = True
                        st.session_state["imp_df"] = df; st.rerun()
                with cb:
                    if st.button("❌ Nenhuma", key="cart_none"):
                        df.loc[df_cartao.index,"importar"] = False
                        st.session_state["imp_df"] = df; st.rerun()

                df_cart_ed = df_cartao[["importar","data","descricao","valor",
                                         "categoria","num_parcelas"]].rename(columns={
                    "importar":"✓","data":"Data","descricao":"Descrição",
                    "valor":"R$","categoria":"Categoria","num_parcelas":"Parcelas"})

                ed = st.data_editor(df_cart_ed,
                    column_config={
                        "✓":        st.column_config.CheckboxColumn(width="small"),
                        "Data":     st.column_config.DateColumn(format="DD/MM/YY", width="small"),
                        "Descrição":st.column_config.TextColumn(width="large"),
                        "R$":       st.column_config.NumberColumn(format="R$ %.2f", width="small"),
                        "Categoria":st.column_config.SelectboxColumn(options=cats, width="medium"),
                        "Parcelas": st.column_config.NumberColumn(min_value=1, max_value=48,
                                        step=1, width="small",
                                        help="Nº de parcelas — editável por linha"),
                    },
                    use_container_width=True, hide_index=True,
                    num_rows="fixed", key="imp_ed_cartao")

                if ed is not None:
                    df.loc[df_cartao.index, "importar"]     = ed["✓"].values
                    df.loc[df_cartao.index, "categoria"]    = ed["Categoria"].values
                    df.loc[df_cartao.index, "num_parcelas"] = ed["Parcelas"].apply(
                        lambda x: max(1, _safe_int(x, 1))).values
                    st.session_state["imp_df"] = df

            st.markdown("</div>", unsafe_allow_html=True)

        # ── Seção Lançamentos (sem box, só label) ─────────────────
        if not df_outros.empty:
            if not df_cartao.empty:
                st.markdown("<div class='imp-sep'></div>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='imp-sec-lbl'>📋 Outros lançamentos — {len(df_outros)} transações</div>",
                unsafe_allow_html=True)

            df_exist = get_lancamentos()
            dups = set()
            if not df_exist.empty:
                for i, row in df_outros.iterrows():
                    # Prioriza _ano/_mes (computados via pd.to_datetime, sempre confiáveis)
                    # sobre ano/mes (que podem vir zerados dependendo do importador).
                    # Isso garante que transações de meses diferentes nunca sejam
                    # marcadas como duplicatas por conta de data mal parseada.
                    ano_r = _safe_int(row.get("_ano", row.get("ano", 0)))
                    mes_r = _safe_int(row.get("_mes", row.get("mes", 0)))
                    if ano_r == 0 or mes_r == 0:
                        continue  # data inválida — não marcar como duplicata
                    m = ((df_exist["ano"].astype(int) == ano_r) &
                         (df_exist["mes"].astype(int) == mes_r) &
                         (df_exist["valor"].astype(float).round(2) == round(_safe_float(row["valor"]),2)) &
                         (df_exist["tipo"] == row["tipo"]))
                    if m.any(): dups.add(i)
            # Desmarcar duplicatas e forçar rerun para o editor refletir
            _dups_key = f"_dups_notified_{st.session_state.get('imp_filename', 'default')}"
            if dups and _dups_key not in st.session_state:
                df.loc[list(dups), "importar"] = False
                st.session_state["imp_df"] = df
                st.session_state[_dups_key] = len(dups)
                st.rerun()
            if dups:
                _n_dups = st.session_state.get(_dups_key, len(dups))
                st.markdown(f"<div class='imp-warn'>⚠️ {_n_dups} possível(is) "
                            f"duplicata(s) desmarcada(s) automaticamente.</div>",
                            unsafe_allow_html=True)
            df_outros = df_view[~mask_cartao].copy()

            la, lb, _ = st.columns([1,1,6])
            with la:
                if st.button("✅ Todas",   key="lanc_all"):
                    df.loc[df_outros.index,"importar"] = True
                    st.session_state["imp_df"] = df; st.rerun()
            with lb:
                if st.button("❌ Nenhuma", key="lanc_none"):
                    df.loc[df_outros.index,"importar"] = False
                    st.session_state["imp_df"] = df; st.rerun()

            edl = st.data_editor(
                df_outros[["importar","data","descricao","valor","tipo","categoria","forma_pagamento"]]
                    .rename(columns={"importar":"✓","data":"Data","descricao":"Descrição",
                                     "valor":"R$","tipo":"Tipo","categoria":"Categoria",
                                     "forma_pagamento":"Forma"}),
                column_config={
                    "✓":    st.column_config.CheckboxColumn(width="small"),
                    "Data": st.column_config.DateColumn(format="DD/MM/YY", width="small"),
                    "Descrição": st.column_config.TextColumn(width="large"),
                    "R$":   st.column_config.NumberColumn(format="R$ %.2f", width="small"),
                    "Tipo": st.column_config.SelectboxColumn(options=["Débito","Crédito"],
                                                              width="small"),
                    "Categoria": st.column_config.SelectboxColumn(options=cats, width="medium"),
                    "Forma":     st.column_config.SelectboxColumn(options=FORMAS, width="small"),
                },
                use_container_width=True, hide_index=True,
                num_rows="fixed", key="imp_ed_lanc")

            if edl is not None:
                df.loc[df_outros.index, "importar"]        = edl["✓"].values
                df.loc[df_outros.index, "categoria"]       = edl["Categoria"].values
                df.loc[df_outros.index, "tipo"]            = edl["Tipo"].values
                df.loc[df_outros.index, "forma_pagamento"] = edl["Forma"].values
                st.session_state["imp_df"] = df

        # ── Footer + botão importar ───────────────────────────────
        n_sel_cart = int(df[mask_cartao]["importar"].sum()) if not df_cartao.empty else 0
        n_sel_lanc = int(df[~mask_cartao]["importar"].sum()) if not df_outros.empty else 0
        n_sel      = n_sel_cart + n_sel_lanc
        tot_sel    = df[df["importar"]]["valor"].sum()

        st.markdown(f"""<div class='imp-footer'>
            <span style='color:rgba(235,235,245,.4)'>Selecionadas:</span>
            <strong style='color:#FFF'>{n_sel}</strong>
            <span style='color:rgba(235,235,245,.1)'>|</span>
            <span style='color:#FF9F0A'>💳 {n_sel_cart} cartão</span>
            <span style='color:rgba(235,235,245,.1)'>|</span>
            <span style='color:#0A84FF'>📋 {n_sel_lanc} lançamentos</span>
            <span style='color:rgba(235,235,245,.1)'>|</span>
            <span style='color:rgba(235,235,245,.5)'>Total: {brl(tot_sel)}</span>
        </div>""", unsafe_allow_html=True)

        if n_sel == 0:
            st.warning("Selecione ao menos uma transação para importar.")
            return

        if st.button(f"💾 Importar {n_sel} transação(ões)",
                     type="primary", use_container_width=True, key="btn_importar"):
            with st.spinner("Importando…"):
                erros, ok_cart, ok_lanc = [], 0, 0
                cartao_nome = st.session_state.get("imp_cartao_nome","")

                max_cart = _max_id(get_cartao_compras)
                for _, row in df[mask_cartao & df["importar"]].iterrows():
                    try:
                        ok, err = add_cartao_compra(
                            cartao_nome, str(row["descricao"]), str(row["categoria"]),
                            _safe_float(row["valor"]),
                            _safe_int(row.get("num_parcelas",1),1),
                            _safe_int(row.get("ano", row.get("_ano",0))),
                            _safe_int(row.get("mes", row.get("_mes",0))),
                        )
                        if ok: ok_cart += 1
                        else:  erros.append(err or f"Erro: {row['descricao']}")
                    except Exception as e: erros.append(str(e))

                max_lanc = _max_id(get_lancamentos)
                for _, row in df[~mask_cartao & df["importar"]].iterrows():
                    try:
                        ok, err = add_lancamento(
                            _safe_int(row.get("ano", row.get("_ano",0))),
                            _safe_int(row.get("mes", row.get("_mes",0))),
                            str(row["descricao"]), str(row["categoria"]),
                            str(row["tipo"]),      _safe_float(row["valor"]),
                            "",                    str(row.get("forma_pagamento","Outros")),
                        )
                        if ok: ok_lanc += 1
                        else:  erros.append(err or f"Erro: {row['descricao']}")
                    except Exception as e: erros.append(str(e))

                # captura IDs novos
                df_nc = _novos_registros(get_cartao_compras, max_cart)
                df_nl = _novos_registros(get_lancamentos,    max_lanc)
                ids_cart_str = ",".join(str(x) for x in df_nc["id"].tolist()) if not df_nc.empty else ""
                ids_lanc_str = ",".join(str(x) for x in df_nl["id"].tolist()) if not df_nl.empty else ""

                # Log permanente com IDs
                if _has_log and (ok_cart + ok_lanc) > 0:
                    try:
                        meses_str = ", ".join(
                            f"{MESES_PT.get(m,m)}/{str(a)[2:]}"
                            for a,m in sorted(set(zip(
                                df[df["importar"]]["_ano"].tolist(),
                                df[df["importar"]]["_mes"].tolist())))
                        )
                        _ok_log, _err_log = _st.add_import_log(
                            username,
                            st.session_state.get("imp_filename","—"),
                            st.session_state.get("imp_banco","—"),
                            ok_lanc, ok_cart, meses_str,
                            ids_lanc_str, ids_cart_str
                        )
                        if not _ok_log:
                            erros.append(f"⚠️ Histórico não salvo: {_err_log}")
                    except Exception as _e_log:
                        erros.append(f"⚠️ Erro ao salvar histórico: {_e_log}")

            st.session_state.update({
                "imp_ok_cart": ok_cart, "imp_ok_lanc": ok_lanc,
                "imp_erros":   erros,   "imp_step":    _STEP_DONE,
            })
            st.rerun()

    # ══════════════════════════════════════════════════════════════
    # STEP 3 — CONCLUÍDO
    # ══════════════════════════════════════════════════════════════
    elif step == _STEP_DONE:
        ok_cart = st.session_state.get("imp_ok_cart", 0)
        ok_lanc = st.session_state.get("imp_ok_lanc", 0)
        erros   = st.session_state.get("imp_erros",   [])

        st.markdown(
            f"<div class='imp-success'>"
            f"✅ {ok_cart + ok_lanc} transação(ões) importada(s) com sucesso!</div>",
            unsafe_allow_html=True)

        d1,d2,d3 = st.columns(3)
        _stat_card(d1, str(ok_cart), "💳 No Cartão",   "", "#FF9F0A")
        _stat_card(d2, str(ok_lanc), "📋 Lançamentos", "", "#0A84FF")
        _stat_card(d3, str(len(erros)), "⚠️ Erros",    "",
                   "#FF453A" if erros else "#8E8E93")

        if erros:
            with st.expander(f"⚠️ Ver {len(erros)} erro(s)"):
                for e in erros: st.caption(e)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        na, nb, nc = st.columns(3)
        with na:
            if st.button("📥 Nova importação", use_container_width=True):
                _reset(); st.rerun()
        with nb:
            if st.button("💳 Ir para Cartões", use_container_width=True):
                _reset(); st.session_state["aba"] = "Cartões"; st.rerun()
        with nc:
            if st.button("📊 Dashboard", use_container_width=True, type="primary"):
                _reset(); st.session_state["aba"] = "Dashboard"; st.rerun()

        st.caption("↩ Para excluir transações desta importação, clique em "
                   "**Nova importação** e expanda a linha no Histórico.")