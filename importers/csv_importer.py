"""importers/csv_importer.py — Parser CSV multi-banco com detecção automática."""

from __future__ import annotations
import io
import re
from datetime import date, datetime
import pandas as pd

from importers.category_matcher import sugerir_categoria, sugerir_forma_pagamento

BANCOS_SUPORTADOS = [
    "Nubank Crédito", "Nubank Conta", "Banco Inter",
    "Itaú", "Bradesco", "C6 Bank",
]


def _detect_bank(header: str, sample: str) -> str | None:
    h = header.lower()
    if "nubank" in h or ("date" in h and "title" in h and "amount" in h):
        if "category" in h:
            return "Nubank Crédito"
        return "Nubank Conta"
    if "inter" in h or ("data lancamento" in h and "historico" in h):
        return "Banco Inter"
    if "lançamento" in h and "débito" in h and "crédito" in h:
        return "Itaú"
    if "data" in h and "historico" in h and "docto" in h:
        return "Bradesco"
    if "c6" in h:
        return "C6 Bank"
    return None


def _parse_brl(value) -> float:
    if pd.isna(value):
        return 0.0
    s = str(value).strip().replace(" ", "")
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    s = s.replace("R$", "").strip()
    if re.search(r"\d\.\d{3},", s):
        s = s.replace(".", "").replace(",", ".")
    elif "," in s and "." not in s:
        s = s.replace(",", ".")
    elif "," in s and "." in s:
        if s.index(",") > s.index("."):
            s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def _to_date(value) -> date:
    if isinstance(value, (date, datetime)):
        return value if isinstance(value, date) else value.date()
    s = str(value).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return date.today()


def _parse_nubank_credito(df_raw: pd.DataFrame) -> pd.DataFrame:
    df_raw.columns = [c.lower().strip() for c in df_raw.columns]
    rows = []
    for _, r in df_raw.iterrows():
        d = _to_date(r.get("date", r.get("data", "")))
        desc = str(r.get("title", r.get("descricao", ""))).strip()
        val = abs(_parse_brl(r.get("amount", r.get("valor", 0))))
        cat = str(r.get("category", "")).strip() or sugerir_categoria(desc, "Débito")
        rows.append({
            "data": d, "ano": d.year, "mes": d.month,
            "descricao": desc, "valor": val,
            "tipo": "Débito", "categoria": cat,
            "forma_pagamento": sugerir_forma_pagamento(desc, "Débito"),
            "importar": True,
        })
    return pd.DataFrame(rows)


def _parse_nubank_conta(df_raw: pd.DataFrame) -> pd.DataFrame:
    df_raw.columns = [c.lower().strip() for c in df_raw.columns]
    rows = []
    for _, r in df_raw.iterrows():
        d = _to_date(r.get("data", ""))
        desc = str(r.get("descricao", r.get("description", ""))).strip()
        val = _parse_brl(r.get("valor", r.get("amount", 0)))
        tipo = "Crédito" if val > 0 else "Débito"
        rows.append({
            "data": d, "ano": d.year, "mes": d.month,
            "descricao": desc, "valor": abs(val),
            "tipo": tipo, "categoria": sugerir_categoria(desc, tipo),
            "forma_pagamento": sugerir_forma_pagamento(desc, tipo),
            "importar": True,
        })
    return pd.DataFrame(rows)


def _parse_inter(df_raw: pd.DataFrame) -> pd.DataFrame:
    df_raw.columns = [c.lower().strip() for c in df_raw.columns]
    rows = []
    for _, r in df_raw.iterrows():
        d = _to_date(r.get("data lançamento", r.get("data", "")))
        desc = str(r.get("histórico", r.get("descricao", ""))).strip()
        val = _parse_brl(r.get("valor", 0))
        tipo = "Crédito" if val > 0 else "Débito"
        rows.append({
            "data": d, "ano": d.year, "mes": d.month,
            "descricao": desc, "valor": abs(val),
            "tipo": tipo, "categoria": sugerir_categoria(desc, tipo),
            "forma_pagamento": sugerir_forma_pagamento(desc, tipo),
            "importar": True,
        })
    return pd.DataFrame(rows)


def _parse_itau(lines: list[str]) -> pd.DataFrame:
    data_lines = [l for l in lines if re.match(r"\d{2}/\d{2}/\d{4}", l.strip())]
    rows = []
    for line in data_lines:
        parts = [p.strip() for p in line.split(";") if p.strip()]
        if len(parts) < 3:
            continue
        d = _to_date(parts[0])
        desc = parts[1]
        deb = _parse_brl(parts[2]) if len(parts) > 2 else 0.0
        cre = _parse_brl(parts[3]) if len(parts) > 3 else 0.0
        if cre > 0:
            val, tipo = cre, "Crédito"
        else:
            val, tipo = abs(deb), "Débito"
        if val == 0:
            continue
        rows.append({
            "data": d, "ano": d.year, "mes": d.month,
            "descricao": desc, "valor": val,
            "tipo": tipo, "categoria": sugerir_categoria(desc, tipo),
            "forma_pagamento": sugerir_forma_pagamento(desc, tipo),
            "importar": True,
        })
    return pd.DataFrame(rows)


def _parse_bradesco(df_raw: pd.DataFrame) -> pd.DataFrame:
    df_raw.columns = [c.lower().strip() for c in df_raw.columns]
    rows = []
    for _, r in df_raw.iterrows():
        d = _to_date(r.get("data", ""))
        desc = str(r.get("histórico", r.get("descricao", ""))).strip()
        deb = abs(_parse_brl(r.get("débito", r.get("debito", 0))))
        cre = abs(_parse_brl(r.get("crédito", r.get("credito", 0))))
        if cre > 0:
            val, tipo = cre, "Crédito"
        else:
            val, tipo = deb, "Débito"
        if val == 0:
            continue
        rows.append({
            "data": d, "ano": d.year, "mes": d.month,
            "descricao": desc, "valor": val,
            "tipo": tipo, "categoria": sugerir_categoria(desc, tipo),
            "forma_pagamento": sugerir_forma_pagamento(desc, tipo),
            "importar": True,
        })
    return pd.DataFrame(rows)


def _parse_c6(df_raw: pd.DataFrame) -> pd.DataFrame:
    return _parse_nubank_conta(df_raw)


def _parse_generico(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Fallback genérico — detecta colunas automaticamente.
    Suporta coluna 'tipo' com valores 'credito'/'debito'.
    """
    df_raw.columns = [c.lower().strip() for c in df_raw.columns]
    col_data  = next((c for c in df_raw.columns if "data" in c), None)
    col_desc  = next((c for c in df_raw.columns
                      if any(x in c for x in ["descri", "histor", "memo", "lancamento"])), None)
    col_valor = next((c for c in df_raw.columns
                      if any(x in c for x in ["valor", "amount", "montante"])), None)
    col_tipo  = next((c for c in df_raw.columns
                      if c in ("tipo", "type", "natureza")), None)
    col_deb   = next((c for c in df_raw.columns if "déb" in c or "deb" in c), None)
    col_cre   = next((c for c in df_raw.columns if "cré" in c or "cred" in c), None)

    if not col_desc:
        raise ValueError("Não foi possível identificar a coluna de descrição no CSV.")

    rows = []
    for _, r in df_raw.iterrows():
        d = _to_date(r[col_data]) if col_data else date.today()
        desc = str(r[col_desc]).strip()

        if col_tipo and str(r[col_tipo]).strip().lower() in ("credito", "crédito", "credit", "entrada", "c"):
            tipo = "Crédito"
            val  = abs(_parse_brl(r[col_valor])) if col_valor else 0.0
        elif col_tipo and str(r[col_tipo]).strip().lower() in ("debito", "débito", "debit", "saida", "saída", "d"):
            tipo = "Débito"
            val  = abs(_parse_brl(r[col_valor])) if col_valor else 0.0
        elif col_deb and col_cre:
            deb = abs(_parse_brl(r[col_deb]))
            cre = abs(_parse_brl(r[col_cre]))
            if cre > 0:
                val, tipo = cre, "Crédito"
            else:
                val, tipo = deb, "Débito"
        elif col_valor:
            raw = _parse_brl(r[col_valor])
            tipo = "Crédito" if raw > 0 else "Débito"
            val  = abs(raw)
        else:
            continue

        if val == 0:
            continue

        rows.append({
            "data": d, "ano": d.year, "mes": d.month,
            "descricao": desc, "valor": val,
            "tipo": tipo,
            "categoria": sugerir_categoria(desc, tipo),
            "forma_pagamento": sugerir_forma_pagamento(desc, tipo),
            "importar": True,
        })
    return pd.DataFrame(rows)


def parse_csv(file_bytes: bytes, bank_hint: str | None = None) -> pd.DataFrame:
    """
    Parseia um CSV de extrato bancário.
    bank_hint: nome do banco (ex: "Itaú") ou None para auto-detectar.
    """
    text = file_bytes.decode("utf-8", errors="replace")
    lines = text.splitlines()

    if not lines:
        raise ValueError("Arquivo CSV vazio.")

    bank = bank_hint
    if not bank:
        header = lines[0] if lines else ""
        bank = _detect_bank(header, "\n".join(lines[:5]))

    if bank == "Itaú":
        df = _parse_itau(lines)
        if df.empty:
            raise ValueError("Nenhuma transação encontrada no formato Itaú.")
        return df

    sep = ";" if text.count(";") > text.count(",") else ","
    try:
        df_raw = pd.read_csv(io.StringIO(text), sep=sep, dtype=str, on_bad_lines="skip")
    except Exception as e:
        raise ValueError(f"Erro ao ler CSV: {e}")

    if df_raw.empty:
        raise ValueError("Nenhuma transação encontrada no CSV.")

    if bank == "Nubank Crédito":
        return _parse_nubank_credito(df_raw)
    elif bank == "Nubank Conta":
        return _parse_nubank_conta(df_raw)
    elif bank == "Banco Inter":
        return _parse_inter(df_raw)
    elif bank == "Bradesco":
        return _parse_bradesco(df_raw)
    elif bank in ("C6 Bank",):
        return _parse_c6(df_raw)
    else:
        return _parse_generico(df_raw)
