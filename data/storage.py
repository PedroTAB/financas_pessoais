import streamlit as st
import pandas as pd
import gspread
import json
import time
from pathlib import Path
from datetime import datetime, date
from google.oauth2.service_account import Credentials


CATEGORIAS_DEBITO = [
    "Moradia", "Subsistência", "Transporte", "Saúde", "Lazer", "Vestuário",
    "Conta", "Eletrônicos", "Streaming", "Educação", "Restaurantes",
    "Viagem", "Assinaturas", "Pets", "Presentes", "Outros"
]
CATEGORIAS_CREDITO = ["Estorno", "Restituição", "Acordo", "Venda", "Premiação", "Outros"]
CATEGORIAS = CATEGORIAS_DEBITO + CATEGORIAS_CREDITO
TIPOS = ["Débito", "Crédito"]
TIPOS_GANHO = ["Salário", "Investimento", "Aluguel", "Freelance", "Outros"]
TIPOS_INV = [
    "Renda Fixa", "Renda Variável", "Tesouro Direto", "CDB", "LCI/LCA",
    "Fundos", "Ações", "FIIs", "Criptomoedas", "Outros"
]
MESES_ABR = {
    1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
}

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

COLS_LANC       = ["id", "username", "ano", "mes", "descricao", "categoria", "tipo", "forma_pagamento", "valor", "grupo_id"]
COLS_GANHO      = ["id", "username", "ano", "mes", "tipo_ganho", "descricao", "valor_liquido", "extras"]
COLS_CARTAO     = ["id", "username", "cartao", "descricao", "categoria", "valor_total", "num_parcelas", "ano_inicio", "mes_inicio", "data_registro"]
COLS_CARTAO_CFG = ["id", "username", "nome", "digitos", "limite", "vencimento", "cor"]
COLS_PERFIS     = ["username", "nome", "avatar", "cor", "password"]
COLS_CATEGORIAS = ["id", "username", "tipo", "nome"]
COLS_USER_CFG   = ["username", "necessidades", "desejos", "poupanca"]
COLS_HISTORICO  = ["id", "username", "timestamp", "entidade", "operacao", "registro_id", "snapshot"]

INSS_FAIXAS = [(1518.00, 0.075), (2793.88, 0.09), (4190.83, 0.12), (8157.41, 0.14)]
INSS_TETO = 908.86
IRRF_FAIXAS = [
    (2259.20, 0.000, 0.00),
    (2826.65, 0.075, 169.44),
    (3751.05, 0.150, 381.44),
    (4664.68, 0.225, 662.77),
    (float("inf"), 0.275, 896.00),
]
IRRF_DED_DEP = 189.59


# ─────────────────────────────────────────────────────────────────────────────
# UTILITÁRIOS
# ─────────────────────────────────────────────────────────────────────────────

def _safe(v):
    """Converte numpy/pandas types para tipos nativos Python antes de enviar ao Sheets."""
    try:
        import numpy as np
        if isinstance(v, np.integer):
            return int(v)
        if isinstance(v, np.floating):
            return float(v)
        if isinstance(v, np.bool_):
            return bool(v)
    except ImportError:
        pass
    return v


def _safe_row(row: list) -> list:
    """Aplica _safe() em todos os elementos de uma linha antes de enviar ao gspread."""
    return [_safe(v) for v in row]


def _parse_num_br(v):
    try:
        s = str(v).strip().replace(" ", "")
        if not s or s in ("", "None"):
            return 0.0
        if "," in s and "." in s:
            return float(s.replace(".", "").replace(",", "."))
        if "," in s:
            return float(s.replace(",", "."))
        return float(s)
    except Exception:
        return 0.0


def _fmt(v):
    return str(round(float(v), 2))


def _safe_username(user_id):
    return str(user_id).strip().lower() if user_id else "default"


def _next_id(recs: list, col: str = "id") -> int:
    """Calcula o próximo ID a partir de uma lista de records — sempre retorna int nativo."""
    if not recs:
        return 1
    ids = []
    for r in recs:
        try:
            ids.append(int(r.get(col, 0) or 0))
        except Exception:
            pass
    return max(ids, default=0) + 1


def calc_inss(bruto: float) -> float:
    inss, ant = 0.0, 0.0
    for lim, aliq in INSS_FAIXAS:
        if bruto <= lim:
            inss += (bruto - ant) * aliq
            break
        inss += (lim - ant) * aliq
        ant = lim
    else:
        inss += (bruto - ant) * INSS_FAIXAS[-1][1]
    return round(min(inss, INSS_TETO), 2)


def calc_irrf(bruto: float, inss: float, deps: int = 0) -> float:
    base = bruto - inss - IRRF_DED_DEP * deps
    for lim, aliq, ded in IRRF_FAIXAS:
        if base <= lim:
            return round(max(base * aliq - ded, 0), 2)
    return 0.0


# ─────────────────────────────────────────────────────────────────────────────
# CONEXÃO COM GOOGLE SHEETS
# ─────────────────────────────────────────────────────────────────────────────

def _ensure_header(ws, cols):
    try:
        vals = ws.get_all_values()
        if not vals:
            ws.update("A1", [cols])
            return
        if vals[0] == cols:
            return
        if len(vals[0]) < len(cols):
            data_rows = vals[1:]
            new_rows = []
            for r in data_rows:
                r = list(r) + [""] * (len(cols) - len(r))
                new_rows.append(r[:len(cols)])
            ws.clear()
            ws.update("A1", [cols] + new_rows)
        else:
            ws.update("A1", [cols])
    except Exception:
        pass


@st.cache_resource(ttl=600)
def _get_worksheets():
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]), scopes=SCOPES
    )
    gc = gspread.authorize(creds)
    sh = gc.open(st.secrets["sheet_name"])

    def _ws(name, cols):
        try:
            ws = sh.worksheet(name)
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet(title=name, rows=10000, cols=max(len(cols), 12))
            ws.append_row(cols)
            return ws
        _ensure_header(ws, cols)
        return ws

    return (
        _ws("lancamentos",    COLS_LANC),
        _ws("ganhos",         COLS_GANHO),
        _ws("cartao_compras", COLS_CARTAO),
        _ws("cartao_config",  COLS_CARTAO_CFG),
        _ws("perfis",         COLS_PERFIS),
        _ws("categorias",     COLS_CATEGORIAS),
        _ws("user_config",    COLS_USER_CFG),
        _ws("historico",      COLS_HISTORICO),
    )


def _wsl():    return _get_worksheets()[0]
def _wsg():    return _get_worksheets()[1]
def _wsc():    return _get_worksheets()[2]
def _wscfg():  return _get_worksheets()[3]
def _wsp():    return _get_worksheets()[4]
def _wscat():  return _get_worksheets()[5]
def _wsucfg(): return _get_worksheets()[6]
def _wshist(): return _get_worksheets()[7]


@st.cache_data(ttl=60, show_spinner=False)
def _cached_records(sheet_kind: str):
    mapping = {
        "lanc":       (_wsl,    COLS_LANC),
        "cartao":     (_wsc,    COLS_CARTAO),
        "cartao_cfg": (_wscfg,  COLS_CARTAO_CFG),
        "perfis":     (_wsp,    COLS_PERFIS),
        "categorias": (_wscat,  COLS_CATEGORIAS),
        "user_config":(_wsucfg, COLS_USER_CFG),
        "historico":  (_wshist, COLS_HISTORICO),
    }
    ws_fn, cols = mapping.get(sheet_kind, (_wsg, COLS_GANHO))
    ws = ws_fn()

    recs = None
    for attempt in range(3):
        try:
            recs = ws.get_all_records(expected_headers=cols)
            break
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                time.sleep(5 * (attempt + 1))
                _get_worksheets.clear()
                ws = ws_fn()
                continue
            break

    if recs is not None:
        return recs

    # fallback: leitura raw
    vals = ws.get_all_values()
    if not vals:
        ws.update("A1", [cols])
        return []
    if vals[0] != cols:
        _ensure_header(ws, cols)
        vals = ws.get_all_values()
    if len(vals) <= 1:
        return []
    out = []
    for r in vals[1:]:
        r = list(r) + [""] * (len(cols) - len(r))
        out.append({c: r[i] for i, c in enumerate(cols)})
    return out


# ─────────────────────────────────────────────────────────────────────────────
# PERFIS
# ─────────────────────────────────────────────────────────────────────────────

def get_perfis() -> dict:
    recs = _cached_records("perfis") or []
    result = {}
    for r in recs:
        u = _safe_username(r.get("username"))
        if u and u != "default":
            result[u] = {
                "nome":   r.get("nome", ""),
                "avatar": r.get("avatar", ""),
                "cor":    r.get("cor", "#0A84FF"),
                "password_hash": r.get("password", ""),
            }
    if not result:
        result = {"pedro": {"nome": "Pedro", "avatar": "💰", "cor": "#0A84FF", "password_hash": ""}}
    return result


def add_perfil(username: str, nome: str, avatar: str, cor: str, password_hash: str = None):
    try:
        username = _safe_username(username)
        nome = nome.strip()
        if not username or not nome:
            return False, "Username e nome são obrigatórios."
        perfis = get_perfis()
        if username in perfis:
            return False, "Esse perfil já existe."
        _wsp().append_row(
            _safe_row([username, nome, avatar or nome[0].upper(), cor or "#0A84FF", password_hash or ""]),
            value_input_option="RAW"
        )
        _cached_records.clear()
        return True, None
    except Exception as e:
        return False, str(e)


def update_perfil(username: str, nome: str, avatar: str, cor: str, password_hash: str = None):
    try:
        username = _safe_username(username)
        ws = _wsp()
        recs = _cached_records("perfis") or []
        for i, r in enumerate(recs, start=2):
            if _safe_username(r.get("username")) == username:
                ws.update(
                    f"A{i}:E{i}",
                    [_safe_row([username, nome.strip(), avatar or nome[0].upper(), cor or "#0A84FF", password_hash or ""])],
                    value_input_option="RAW"
                )
                _cached_records.clear()
                return True, None
        _wsp().append_row(
            _safe_row([username, nome.strip(), avatar or nome[0].upper(), cor or "#0A84FF", password_hash or ""]),
            value_input_option="RAW"
        )
        _cached_records.clear()
        return True, None
    except Exception as e:
        return False, str(e)


def delete_perfil(username: str):
    try:
        username = _safe_username(username)
        ws = _wsp()
        recs = _cached_records("perfis") or []
        for i, r in enumerate(recs, start=2):
            if _safe_username(r.get("username")) == username:
                ws.delete_rows(i)
                _cached_records.clear()
                return True, None
        return False, "Perfil não encontrado."
    except Exception as e:
        return False, str(e)


# ─────────────────────────────────────────────────────────────────────────────
# CATEGORIAS
# ─────────────────────────────────────────────────────────────────────────────

def get_categories(user_id: str) -> dict:
    username = _safe_username(user_id)
    recs = _cached_records("categorias") or []
    user_recs = [r for r in recs if _safe_username(r.get("username")) == username]
    custom_deb  = [r["nome"] for r in user_recs if r.get("tipo") == "debito"  and r.get("nome")]
    custom_cred = [r["nome"] for r in user_recs if r.get("tipo") == "credito" and r.get("nome")]
    all_deb  = list(CATEGORIAS_DEBITO)  + [c for c in custom_deb  if c not in CATEGORIAS_DEBITO]
    all_cred = list(CATEGORIAS_CREDITO) + [c for c in custom_cred if c not in CATEGORIAS_CREDITO]
    return {"debito": all_deb, "credito": all_cred}


def add_category(user_id: str, tipo: str, nome: str) -> bool:
    nome = nome.strip()
    if not nome:
        return False
    cats = get_categories(user_id)
    if nome in cats.get(tipo, []):
        return False
    username = _safe_username(user_id)
    recs = _cached_records("categorias") or []
    nid = _next_id(recs)
    _wscat().append_row(_safe_row([nid, username, tipo, nome]), value_input_option="RAW")
    _cached_records.clear()
    return True


def remove_category(user_id: str, tipo: str, nome: str) -> bool:
    padrao = list(CATEGORIAS_DEBITO) if tipo == "debito" else list(CATEGORIAS_CREDITO)
    if nome in padrao:
        return False
    username = _safe_username(user_id)
    ws = _wscat()
    recs = _cached_records("categorias") or []
    for i, r in enumerate(recs, start=2):
        if (
            _safe_username(r.get("username")) == username
            and r.get("tipo") == tipo
            and r.get("nome") == nome
        ):
            ws.delete_rows(i)
            _cached_records.clear()
            return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# CONFIG 50/30/20
# ─────────────────────────────────────────────────────────────────────────────

_CFG_DEFAULTS = {"necessidades": 50, "desejos": 30, "poupanca": 20}


def get_user_config(user_id: str) -> dict:
    username = _safe_username(user_id)
    recs = _cached_records("user_config") or []
    for r in recs:
        if _safe_username(r.get("username")) == username:
            return {
                "necessidades": int(r.get("necessidades") or 50),
                "desejos":      int(r.get("desejos")      or 30),
                "poupanca":     int(r.get("poupanca")     or 20),
            }
    return dict(_CFG_DEFAULTS)


def save_user_config(user_id: str, cfg: dict) -> None:
    nec = int(cfg.get("necessidades", 50))
    des = int(cfg.get("desejos", 30))
    pou = int(cfg.get("poupanca", 20))
    if nec + des + pou != 100:
        raise ValueError(f"Os percentuais devem somar 100% (atual: {nec + des + pou}%)")
    username = _safe_username(user_id)
    ws = _wsucfg()
    recs = _cached_records("user_config") or []
    for i, r in enumerate(recs, start=2):
        if _safe_username(r.get("username")) == username:
            ws.update(f"A{i}:D{i}", [_safe_row([username, nec, des, pou])], value_input_option="RAW")
            _cached_records.clear()
            return
    ws.append_row(_safe_row([username, nec, des, pou]), value_input_option="RAW")
    _cached_records.clear()


# ─────────────────────────────────────────────────────────────────────────────
# HISTÓRICO
# ─────────────────────────────────────────────────────────────────────────────

def registrar_historico(user_id: str, entidade: str, operacao: str, registro_id: int, snapshot: dict) -> None:
    try:
        username = _safe_username(user_id)
        recs = _cached_records("historico") or []
        nid = _next_id(recs)
        _wshist().append_row(
            _safe_row([
                nid, username,
                datetime.now().isoformat(timespec="seconds"),
                entidade, operacao, int(registro_id),
                json.dumps(snapshot, ensure_ascii=False),
            ]),
            value_input_option="RAW",
        )
        _cached_records.clear()
    except Exception:
        pass


def get_historico(user_id: str, limit: int = 100) -> list:
    username = _safe_username(user_id)
    recs = _cached_records("historico") or []
    user_hist = [r for r in recs if _safe_username(r.get("username")) == username]
    result = []
    for r in user_hist:
        try:
            snap = json.loads(r.get("snapshot", "{}")) if isinstance(r.get("snapshot"), str) else {}
        except Exception:
            snap = {}
        result.append({
            "id":        r.get("registro_id"),
            "timestamp": r.get("timestamp", ""),
            "entidade":  r.get("entidade", ""),
            "operacao":  r.get("operacao", ""),
            "snapshot":  snap,
        })
    return list(reversed(result[-limit:]))


# ─────────────────────────────────────────────────────────────────────────────
# LANÇAMENTOS
# ─────────────────────────────────────────────────────────────────────────────

def get_lancamentos(user_id=None, *args, **kwargs) -> pd.DataFrame:
    username = _safe_username(user_id)
    recs = _cached_records("lanc")
    if not recs:
        return pd.DataFrame(columns=COLS_LANC)
    df = pd.DataFrame(recs)
    for c in COLS_LANC:
        if c not in df.columns:
            df[c] = ""
    df = df[COLS_LANC].copy()
    df["username"] = df["username"].fillna("").astype(str).str.strip().str.lower()
    df = df[df["username"] == username].copy()
    if df.empty:
        return pd.DataFrame(columns=COLS_LANC)
    df["ano"]   = pd.to_numeric(df["ano"],   errors="coerce").fillna(0).astype(int)
    df["mes"]   = pd.to_numeric(df["mes"],   errors="coerce").fillna(0).astype(int)
    df["valor"] = df["valor"].apply(_parse_num_br)
    df["id"]    = pd.to_numeric(df["id"],    errors="coerce").fillna(0).astype(int)
    df["grupo_id"]        = df["grupo_id"].fillna("").astype(str)
    df["forma_pagamento"] = df["forma_pagamento"].fillna("").astype(str)
    return df


def add_lancamento(user_id, ano, mes, desc, cat, tipo, valor, grupo_id="", forma_pagamento=""):
    try:
        username = _safe_username(user_id)
        recs = _cached_records("lanc") or []
        nid = _next_id(recs)
        _wsl().append_row(
            _safe_row([nid, username, int(ano), int(mes), str(desc), str(cat),
                       str(tipo), str(forma_pagamento), _fmt(valor), str(grupo_id)]),
            value_input_option="RAW"
        )
        _cached_records.clear()
        return True, None
    except Exception as e:
        msg = "Limite de requisições atingido. Tente novamente." if "429" in str(e) else f"Erro ao salvar: {e}"
        return False, msg


def update_lancamento(user_id, id_, ano, mes, desc, cat, tipo, valor, grupo_id="", forma_pagamento=""):
    try:
        username = _safe_username(user_id)
        ws = _wsl()
        recs = _cached_records("lanc") or []
        for i, r in enumerate(recs, start=2):
            if str(r.get("id", "")) == str(id_) and _safe_username(r.get("username")) == username:
                ws.update(
                    f"A{i}:J{i}",
                    [_safe_row([int(id_), username, int(ano), int(mes), str(desc), str(cat),
                                str(tipo), str(forma_pagamento), _fmt(valor), str(grupo_id)])],
                    value_input_option="RAW"
                )
                _cached_records.clear()
                return True, None
        return False, "Registro não encontrado para este perfil."
    except Exception as e:
        msg = "Limite de requisições atingido. Tente novamente." if "429" in str(e) else f"Erro ao atualizar: {e}"
        return False, msg


def delete_lancamento(user_id, id_):
    try:
        username = _safe_username(user_id)
        ws = _wsl()
        recs = _cached_records("lanc") or []
        for i, r in enumerate(recs, start=2):
            if str(r.get("id", "")) == str(id_) and _safe_username(r.get("username")) == username:
                ws.delete_rows(i)
                _cached_records.clear()
                return True, None
        return False, "Registro não encontrado para este perfil."
    except Exception as e:
        msg = "Limite de requisições atingido. Tente novamente." if "429" in str(e) else f"Erro ao excluir: {e}"
        return False, msg


# ─────────────────────────────────────────────────────────────────────────────
# GANHOS
# ─────────────────────────────────────────────────────────────────────────────

def get_ganhos(user_id=None, *args, **kwargs) -> pd.DataFrame:
    username = _safe_username(user_id)
    recs = _cached_records("ganho")
    if not recs:
        return pd.DataFrame(columns=COLS_GANHO)
    df = pd.DataFrame(recs)
    for c in COLS_GANHO:
        if c not in df.columns:
            df[c] = ""
    df = df[COLS_GANHO].copy()
    df["username"] = df["username"].fillna("").astype(str).str.strip().str.lower()
    df = df[df["username"] == username].copy()
    if df.empty:
        return pd.DataFrame(columns=COLS_GANHO)
    for c in ["ano", "mes", "id"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
    df["valor_liquido"] = df["valor_liquido"].apply(_parse_num_br)
    df["extras"] = df["extras"].apply(lambda x: json.loads(x) if x and x != "" else {})
    return df


def add_ganho(user_id, ano, mes, tipo_ganho, desc, valor_liq, extras: dict):
    try:
        username = _safe_username(user_id)
        recs = _cached_records("ganho") or []
        nid = _next_id(recs)
        _wsg().append_row(
            _safe_row([nid, username, int(ano), int(mes), str(tipo_ganho), str(desc),
                       _fmt(valor_liq), json.dumps(extras, ensure_ascii=False)]),
            value_input_option="RAW"
        )
        _cached_records.clear()
        return True, None
    except Exception as e:
        msg = "Limite de requisições atingido. Tente novamente." if "429" in str(e) else f"Erro ao salvar: {e}"
        return False, msg


def update_ganho(user_id, id_, ano, mes, tipo_ganho, desc, valor_liq, extras: dict):
    try:
        username = _safe_username(user_id)
        ws = _wsg()
        recs = _cached_records("ganho") or []
        for i, r in enumerate(recs, start=2):
            if str(r.get("id", "")) == str(id_) and _safe_username(r.get("username")) == username:
                ws.update(
                    f"A{i}:H{i}",
                    [_safe_row([int(id_), username, int(ano), int(mes), str(tipo_ganho),
                                str(desc), _fmt(valor_liq), json.dumps(extras, ensure_ascii=False)])],
                    value_input_option="RAW"
                )
                _cached_records.clear()
                return True, None
        return False, "Registro não encontrado para este perfil."
    except Exception as e:
        msg = "Limite de requisições atingido. Tente novamente." if "429" in str(e) else f"Erro ao atualizar: {e}"
        return False, msg


def delete_ganho(user_id, id_):
    try:
        username = _safe_username(user_id)
        ws = _wsg()
        recs = _cached_records("ganho") or []
        for i, r in enumerate(recs, start=2):
            if str(r.get("id", "")) == str(id_) and _safe_username(r.get("username")) == username:
                ws.delete_rows(i)
                _cached_records.clear()
                return True, None
        return False, "Registro não encontrado para este perfil."
    except Exception as e:
        msg = "Limite de requisições atingido. Tente novamente." if "429" in str(e) else f"Erro ao excluir: {e}"
        return False, msg


# ─────────────────────────────────────────────────────────────────────────────
# CARTÃO
# ─────────────────────────────────────────────────────────────────────────────

def get_cartao_compras(user_id=None, *args, **kwargs) -> pd.DataFrame:
    username = _safe_username(user_id)
    raw = _cached_records("cartao")
    if not raw:
        return pd.DataFrame(columns=COLS_CARTAO)
    df = pd.DataFrame(raw)
    for c in COLS_CARTAO:
        if c not in df.columns:
            df[c] = ""
    df = df[COLS_CARTAO].copy()
    df["username"] = df["username"].fillna("").astype(str).str.strip().str.lower()
    df = df[df["username"] == username].copy()
    if df.empty:
        return pd.DataFrame(columns=COLS_CARTAO)
    for c in ["id", "num_parcelas", "ano_inicio", "mes_inicio"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
    df["valor_total"] = pd.to_numeric(df["valor_total"], errors="coerce").fillna(0.0)
    return df[COLS_CARTAO]


def get_cartoes_cfg(user_id=None, *args, **kwargs):
    try:
        username = _safe_username(user_id)
        recs = _cached_records("cartao_cfg") or []
        return [r for r in recs if _safe_username(r.get("username")) == username]
    except Exception:
        return []


def add_cartao_cfg(user_id, nome, digitos, limite, vencimento, cor):
    try:
        username = _safe_username(user_id)
        recs = _cached_records("cartao_cfg") or []
        nid = _next_id(recs)
        _wscfg().append_row(
            _safe_row([nid, username, str(nome), str(digitos), float(limite), int(vencimento), str(cor)]),
            value_input_option="RAW"
        )
        _cached_records.clear()
        return True, None
    except Exception as e:
        return False, str(e)


def delete_cartao_cfg(user_id, cfg_id):
    try:
        username = _safe_username(user_id)
        ws = _wscfg()
        recs = _cached_records("cartao_cfg") or []
        for i, r in enumerate(recs, start=2):
            if str(r.get("id", "")) == str(cfg_id) and _safe_username(r.get("username")) == username:
                ws.delete_rows(i)
                _cached_records.clear()
                return True, None
        return False, "Cartão não encontrado para este perfil."
    except Exception as e:
        return False, str(e)


def add_cartao_compra(user_id, cartao, descricao, categoria, valor_total, num_parcelas, ano_inicio, mes_inicio):
    try:
        username = _safe_username(user_id)
        recs = _cached_records("cartao") or []
        nid = _next_id(recs)
        _wsc().append_row(
            _safe_row([nid, username, str(cartao), str(descricao), str(categoria),
                       _fmt(valor_total), int(num_parcelas), int(ano_inicio), int(mes_inicio),
                       datetime.now().isoformat()]),
            value_input_option="RAW"
        )
        _cached_records.clear()
        return True, None
    except Exception as e:
        msg = "Limite de requisições atingido. Tente novamente." if "429" in str(e) else f"Erro ao salvar: {e}"
        return False, msg


def update_cartao_compra(user_id, id_, cartao, descricao, categoria, valor_total, num_parcelas, ano_inicio, mes_inicio):
    try:
        username = _safe_username(user_id)
        ws = _wsc()
        recs = _cached_records("cartao") or []
        for i, r in enumerate(recs, start=2):
            if str(r.get("id", "")) == str(id_) and _safe_username(r.get("username")) == username:
                data_reg = r.get("data_registro", "")
                ws.update(
                    f"A{i}:J{i}",
                    [_safe_row([int(id_), username, str(cartao), str(descricao), str(categoria),
                                _fmt(valor_total), int(num_parcelas), int(ano_inicio), int(mes_inicio), data_reg])],
                    value_input_option="RAW"
                )
                _cached_records.clear()
                return True, None
        return False, "Compra não encontrada para este perfil."
    except Exception as e:
        msg = "Limite de requisições atingido. Tente novamente." if "429" in str(e) else f"Erro ao atualizar: {e}"
        return False, msg


def delete_cartao_compra(user_id, id_):
    try:
        username = _safe_username(user_id)
        ws = _wsc()
        recs = _cached_records("cartao") or []
        for i, r in enumerate(recs, start=2):
            if str(r.get("id", "")) == str(id_) and _safe_username(r.get("username")) == username:
                ws.delete_rows(i)
                _cached_records.clear()
                return True, None
        return False, "Compra não encontrada para este perfil."
    except Exception as e:
        msg = "Limite de requisições atingido. Tente novamente." if "429" in str(e) else f"Erro ao excluir: {e}"
        return False, msg


# ─────────────────────────────────────────────────────────────────────────────
# PARCELAS / PROJEÇÃO
# ─────────────────────────────────────────────────────────────────────────────

def get_parcelas_mes(df_compras: pd.DataFrame, ano: int, mes: int) -> pd.DataFrame:
    rows = []
    for _, r in df_compras.iterrows():
        for i in range(int(r["num_parcelas"])):
            mes_abs = (int(r["ano_inicio"]) * 12 + int(r["mes_inicio"]) - 1) + i
            ano_parcela = mes_abs // 12
            mes_parcela = (mes_abs % 12) + 1
            if ano_parcela == ano and mes_parcela == mes:
                valor_p = round(float(r["valor_total"]) / int(r["num_parcelas"]), 2)
                rows.append({
                    "id_compra": int(r["id"]), "cartao": r["cartao"],
                    "descricao": r["descricao"], "categoria": r["categoria"],
                    "valor_parcela": valor_p, "parcela_atual": i + 1,
                    "total_parcelas": int(r["num_parcelas"]),
                    "parcelas_restantes": int(r["num_parcelas"]) - (i + 1),
                })
    if not rows:
        return pd.DataFrame(columns=["id_compra", "cartao", "descricao", "categoria",
                                     "valor_parcela", "parcela_atual", "total_parcelas", "parcelas_restantes"])
    return pd.DataFrame(rows)


def get_total_cartao_mes(df_compras: pd.DataFrame, ano: int, mes: int) -> float:
    df = get_parcelas_mes(df_compras, ano, mes)
    return float(df["valor_parcela"].sum()) if not df.empty else 0.0


def get_projecao_cartao(df_compras: pd.DataFrame, meses: int = 6) -> pd.DataFrame:
    today = date.today()
    rows = []
    cur_a, cur_m = today.year, today.month
    for _ in range(meses):
        total = get_total_cartao_mes(df_compras, cur_a, cur_m)
        rows.append({
            "ano": cur_a, "mes": cur_m,
            "mes_label": f"{MESES_ABR[cur_m]}/{str(cur_a)[2:]}",
            "total": total,
        })
        cur_m += 1
        if cur_m > 12:
            cur_m = 1
            cur_a += 1
    return pd.DataFrame(rows)

# ══════════════════════════════════════════════════════════════════════════════
# METAS E RESERVAS
# ══════════════════════════════════════════════════════════════════════════════

COLS_META = [
    "id", "username", "nome", "tipo", "valor_alvo",
    "valor_atual", "prazo_ano", "prazo_mes", "cor", "icone", "ativa",
]

TIPOS_META = [
    "Reserva de Emergência",
    "Meta de Compra",
    "Meta de Poupança",
    "Quitação de Dívida",
    "Outros",
]

ICONES_META = ["🎯", "🛒", "💰", "💳", "✈️", "🏠", "🚗", "📱", "🎓", "❤️"]


def _wsm():
    """Worksheet de metas (índice 4)."""
    try:
        return _get_worksheets_ext()[0]
    except Exception:
        return None


@st.cache_resource(ttl=600)
def _get_worksheets_ext():
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]), scopes=SCOPES
    )
    gc = gspread.authorize(creds)
    sh = gc.open(st.secrets["sheet_name"])

    def _ws(name, cols):
        try:
            return sh.worksheet(name)
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet(title=name, rows=5000, cols=len(cols))
            ws.append_row(cols)
            return ws

    return (_ws("metas", COLS_META),)


@st.cache_data(ttl=60, show_spinner=False)
def _cached_metas():
    try:
        ws = _wsm()
        if ws is None:
            return []
        return ws.get_all_records(expected_headers=COLS_META)
    except Exception:
        return []


def get_metas(username: str) -> "pd.DataFrame":
    recs = _cached_metas()
    df = pd.DataFrame(recs, columns=COLS_META) if recs else pd.DataFrame(columns=COLS_META)
    if df.empty:
        return df
    df = df[df["username"] == username].copy()
    for col in ["valor_alvo", "valor_atual"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    for col in ["prazo_ano", "prazo_mes"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    df["ativa"] = df["ativa"].astype(str).str.strip().str.upp

# ══════════════════════════════════════════════════════════════════════════════
# IMPORTAÇÃO
# ══════════════════════════════════════════════════════════════════════════════

import pandas as pd
from datetime import datetime


# ─────────────────────────────────────────────────────────────────────────────
# ABA imports_log
# ─────────────────────────────────────────────────────────────────────────────
_COLS_IMP = [
    "id", "username", "data_hora", "arquivo", "banco",
    "n_lancamentos", "n_cartao", "meses",
    "ids_lancamentos", "ids_cartao",
]


@st.cache_resource
def _sh_imports_log():
    """Abre o Spreadsheet via gspread (independente da versão do storage.py)."""
    import gspread as _gspread
    from google.oauth2.service_account import Credentials as _Creds
    _SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
               "https://www.googleapis.com/auth/drive"]
    _creds = _Creds.from_service_account_info(
        dict(st.secrets["gcp_service_account"]), scopes=_SCOPES)
    _gc = _gspread.authorize(_creds)
    return _gc.open(st.secrets["sheet_name"])


def _ws_imp_log():
    """Retorna (criando se necessário) a aba imports_log."""
    sh = _sh_imports_log()
    try:
        return sh.worksheet("imports_log")
    except Exception:
        ws = sh.add_worksheet(title="imports_log", rows=5000, cols=len(_COLS_IMP))
        ws.append_row(_COLS_IMP)
        return ws


def add_import_log(username: str, arquivo: str, banco: str,
                   n_lanc: int, n_cart: int, meses: str,
                   ids_lanc_str: str = "", ids_cart_str: str = ""):
    """Registra uma importação na aba imports_log."""
    try:
        ws = _ws_imp_log()
        recs = ws.get_all_records(expected_headers=_COLS_IMP)
        nid = max((int(r.get("id", 0)) for r in recs), default=0) + 1
        hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ws.append_row([
            nid, username, hora, arquivo, banco,
            int(n_lanc), int(n_cart), meses,
            str(ids_lanc_str), str(ids_cart_str),
        ], value_input_option="RAW")
        return True, None
    except Exception as e:
        return False, str(e)


def get_import_log(username: str) -> pd.DataFrame:
    """Lê o histórico de importações do usuário (leitura direta, sem cache)."""
    try:
        ws  = _ws_imp_log()
        recs = ws.get_all_records(expected_headers=_COLS_IMP)
        if not recs:
            return pd.DataFrame(columns=_COLS_IMP)
        df = pd.DataFrame(recs)
        for c in ["id", "n_lancamentos", "n_cartao"]:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
        df = df[df["username"] == username].copy()
        df = df.sort_values("data_hora", ascending=False).reset_index(drop=True)
        return df
    except Exception:
        return pd.DataFrame(columns=_COLS_IMP)


def update_import_log_counts(log_id: int, n_lanc: int, n_cart: int):
    """Atualiza os contadores de uma entrada do log após deleções."""
    try:
        ws = _ws_imp_log()
        cell = ws.find(str(log_id), in_column=1)
        if cell:
            # Colunas: id(1) username(2) data_hora(3) arquivo(4) banco(5)
            #          n_lancamentos(6) n_cartao(7) meses(8) ids_l(9) ids_c(10)
            ws.update_cell(cell.row, 6, int(n_lanc))
            ws.update_cell(cell.row, 7, int(n_cart))
    except Exception:
        pass


def delete_import_log_entry(log_id: int):
    """Remove uma entrada do histórico (só o log, NÃO as transações)."""
    try:
        ws = _ws_imp_log()
        cell = ws.find(str(log_id), in_column=1)
        if cell:
            ws.delete_rows(cell.row)
            return True, None
        return False, "Entrada não encontrada."
    except Exception as e:
        return False, str(e)


def get_import_transactions(username: str,
                            ids_lanc_str: str,
                            ids_cart_str: str):
    """
    Busca as transações de uma importação pelos IDs salvos no log.
    Suporta storage.py com e sem parâmetro username.
    NÃO chama _cached_records.clear() para evitar loop infinito.
    """
    def _parse(s):
        return [int(x.strip()) for x in str(s).split(",")
                if x.strip().isdigit()]

    def _fetch_df(fn, uid):
        """Tenta fn(username); se falhar por assinatura, tenta fn()."""
        try:
            df = fn(uid)
            return df if df is not None else pd.DataFrame()
        except TypeError:
            try:
                df = fn()
                return df if df is not None else pd.DataFrame()
            except Exception:
                return pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    lanc_ids = _parse(ids_lanc_str)
    cart_ids = _parse(ids_cart_str)
    df_lanc  = pd.DataFrame()
    df_cart  = pd.DataFrame()

    if lanc_ids:
        all_l = _fetch_df(get_lancamentos, username)
        if not all_l.empty and "id" in all_l.columns:
            all_l["id"] = pd.to_numeric(all_l["id"], errors="coerce")
            df_lanc = all_l[all_l["id"].isin(lanc_ids)].copy()

    if cart_ids:
        all_c = _fetch_df(get_cartao_compras, username)
        if not all_c.empty and "id" in all_c.columns:
            all_c["id"] = pd.to_numeric(all_c["id"], errors="coerce")
            df_cart = all_c[all_c["id"].isin(cart_ids)].copy()

    return df_lanc, df_cart
