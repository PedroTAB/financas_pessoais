"""importers/ofx_importer.py — Parser de arquivos OFX/OFC (padrão bancário BR)."""

from __future__ import annotations
import re
from datetime import datetime
from typing import Generator
import pandas as pd
from importers.category_matcher import sugerir_categoria, sugerir_tipo


# ── Parser OFX manual (sem dependência externa) ───────────────────────────────
# Evitamos ofxparse pois tem problemas com encoding de bancos BR

def _tag(content: str, tag: str) -> list[str]:
    """Extrai todos os valores de uma tag SGML/OFX."""
    pattern = rf"<{tag}>([^<\n\r]*)"
    return re.findall(pattern, content, re.IGNORECASE)


def _blocos(content: str, tag: str) -> list[str]:
    """Extrai blocos delimitados por <TAG>...</TAG>."""
    pattern = rf"<{tag}>(.*?)</{tag}>"
    return re.findall(pattern, content, re.IGNORECASE | re.DOTALL)


def _parse_date(raw: str) -> datetime:
    """Converte datas OFX: YYYYMMDDHHMMSS[.xxx][TZ] → datetime."""
    raw = raw.strip()[:14].ljust(14, "0")
    try:
        return datetime.strptime(raw, "%Y%m%d%H%M%S")
    except ValueError:
        return datetime.strptime(raw[:8], "%Y%m%d")


def _detect_encoding(raw: bytes) -> str:
    """Detecta encoding do arquivo OFX."""
    for enc in ("utf-8-sig", "latin-1", "cp1252", "utf-8"):
        try:
            raw.decode(enc)
            return enc
        except (UnicodeDecodeError, LookupError):
            continue
    return "latin-1"


def parse_ofx(file_bytes: bytes) -> pd.DataFrame:
    """
    Parseia um arquivo OFX/OFC e retorna DataFrame pronto para preview.

    Colunas retornadas:
        data (date), descricao (str), valor (float), tipo (str),
        categoria (str), forma_pagamento (str), importar (bool)
    """
    enc     = _detect_encoding(file_bytes)
    content = file_bytes.decode(enc, errors="replace")

    # Tentar extrair transações da seção STMTTRN
    transacoes: list[dict] = []
    blocos_tx = _blocos(content, "STMTTRN")

    if not blocos_tx:
        raise ValueError(
            "Nenhuma transação encontrada no arquivo OFX. "
            "Verifique se o arquivo é um extrato bancário válido."
        )

    for bloco in blocos_tx:
        raw_date  = (_tag(bloco, "DTPOSTED") or [""])[0].strip()
        raw_amt   = (_tag(bloco, "TRNAMT")  or ["0"])[0].strip().replace(",", ".")
        raw_memo  = (_tag(bloco, "MEMO")    or [""])[0].strip()
        raw_name  = (_tag(bloco, "NAME")    or [""])[0].strip()
        raw_type  = (_tag(bloco, "TRNTYPE") or [""])[0].strip().upper()
        raw_id    = (_tag(bloco, "FITID")   or [""])[0].strip()

        if not raw_date or not raw_amt:
            continue

        try:
            dt    = _parse_date(raw_date)
            valor = float(raw_amt)
        except (ValueError, TypeError):
            continue

        descricao = raw_memo or raw_name or "Sem descrição"
        # Normalizar descrição: remover espaços extras
        descricao = " ".join(descricao.split())

        # Determinar tipo: OFX usa CREDIT/DEBIT, mas também usamos o sinal
        if raw_type in ("CREDIT", "DEP", "INT", "DIV"):
            tipo = "Crédito"
            valor = abs(valor)
        elif raw_type in ("DEBIT", "CHECK", "ATM", "FEE", "SRVCHG", "XFER"):
            tipo = "Débito"
            valor = abs(valor)
        else:
            tipo  = sugerir_tipo(descricao, valor)
            valor = abs(valor)

        categoria = sugerir_categoria(descricao, tipo)

        transacoes.append({
            "data":             dt.date(),
            "ano":              dt.year,
            "mes":              dt.month,
            "dia":              dt.day,
            "descricao":        descricao,
            "valor":            round(valor, 2),
            "tipo":             tipo,
            "categoria":        categoria,
            "forma_pagamento":  "Outros" if tipo == "Débito" else "",
            "importar":         True,
            "_fitid":           raw_id,
        })

    if not transacoes:
        raise ValueError("Arquivo OFX lido, mas nenhuma transação válida encontrada.")

    df = pd.DataFrame(transacoes).sort_values("data").reset_index(drop=True)
    return df
