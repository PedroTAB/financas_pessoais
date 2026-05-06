"""data/metas_storage.py - Persistência de Metas e Reservas (Google Sheets)."""
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

COLS_META = [
    "id", "username", "nome", "tipo", "valor_alvo",
    "valor_atual", "prazo_ano", "prazo_mes", "cor", "icone", "ativa",
]

TIPOS_META = [
    "Reserva de Emergencia",
    "Meta de Compra",
    "Meta de Poupanca",
    "Quitacao de Divida",
    "Outros",
]

ICONES_META = ["🎯", "🛒", "💰", "💳", "✈️", "🏠", "🚗", "📱", "🎓", "❤️"]


@st.cache_resource(ttl=600)
def _get_ws_metas():
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]), scopes=SCOPES
    )
    gc = gspread.authorize(creds)
    sh = gc.open(st.secrets["sheet_name"])
    try:
        ws = sh.worksheet("metas")
        # Garante que o header existe
        if ws.row_values(1) != COLS_META:
            ws.update("A1", [COLS_META])
        return ws
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title="metas", rows=5000, cols=len(COLS_META))
        ws.append_row(COLS_META)
        return ws


@st.cache_data(ttl=60, show_spinner=False)
def _cached_metas_recs():
    try:
        ws = _get_ws_metas()
        return ws.get_all_records(expected_headers=COLS_META)
    except Exception:
        return []


def get_metas(username: str) -> pd.DataFrame:
    recs = _cached_metas_recs()
    df   = pd.DataFrame(recs, columns=COLS_META) if recs else pd.DataFrame(columns=COLS_META)
    if df.empty:
        return df
    df = df[df["username"].astype(str) == str(username)].copy()
    for col in ["valor_alvo", "valor_atual"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    for col in ["prazo_ano", "prazo_mes"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    df["ativa"] = df["ativa"].astype(str).str.strip().str.upper().isin(["TRUE", "1", "SIM"])
    return df.reset_index(drop=True)


def _next_id(ws) -> int:
    try:
        recs = ws.get_all_records(expected_headers=COLS_META)
        return max((int(r["id"]) for r in recs if str(r["id"]).isdigit()), default=0) + 1
    except Exception:
        return 1


def add_meta(
    username: str,
    nome: str,
    tipo: str,
    valor_alvo: float,
    valor_atual: float,
    prazo_ano: int,
    prazo_mes: int,
    cor: str,
    icone: str,
) -> tuple:
    try:
        ws  = _get_ws_metas()
        nid = _next_id(ws)
        ws.append_row(
            [nid, str(username), str(nome), str(tipo),
             float(valor_alvo), float(valor_atual),
             int(prazo_ano), int(prazo_mes),
             str(cor), str(icone), "TRUE"],
            value_input_option="RAW",
        )
        _cached_metas_recs.clear()
        return True, None
    except Exception as e:
        return False, str(e)


def update_meta(
    meta_id: int,
    username: str,
    nome: str,
    tipo: str,
    valor_alvo: float,
    valor_atual: float,
    prazo_ano: int,
    prazo_mes: int,
    cor: str,
    icone: str,
    ativa: bool,
) -> tuple:
    try:
        ws   = _get_ws_metas()
        cell = ws.find(str(meta_id), in_column=1)
        if cell is None:
            return False, "Meta nao encontrada."
        ws.update(
            f"A{cell.row}:K{cell.row}",
            [[meta_id, str(username), str(nome), str(tipo),
              float(valor_alvo), float(valor_atual),
              int(prazo_ano), int(prazo_mes),
              str(cor), str(icone), "TRUE" if ativa else "FALSE"]],
            value_input_option="RAW",
        )
        _cached_metas_recs.clear()
        return True, None
    except Exception as e:
        return False, str(e)


def delete_meta(meta_id: int) -> tuple:
    try:
        ws   = _get_ws_metas()
        cell = ws.find(str(meta_id), in_column=1)
        if cell is None:
            return False, "Meta nao encontrada."
        ws.delete_rows(cell.row)
        _cached_metas_recs.clear()
        return True, None
    except Exception as e:
        return False, str(e)


def update_meta_valor_atual(meta_id: int, novo_valor: float) -> tuple:
    try:
        ws   = _get_ws_metas()
        cell = ws.find(str(meta_id), in_column=1)
        if cell is None:
            return False, "Meta nao encontrada."
        ws.update_cell(cell.row, 6, float(novo_valor))   # coluna F = valor_atual
        _cached_metas_recs.clear()
        return True, None
    except Exception as e:
        return False, str(e)
