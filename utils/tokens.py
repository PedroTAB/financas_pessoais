"""utils/tokens.py — design tokens centralizados (paleta, categorias, constantes)."""
from __future__ import annotations


class _MesesDict(dict):
    """Dicionário de meses que aceita tanto chave 1-based (int) quanto índice 0-based.

    Comportamento idêntico ao original {1: "Janeiro", ..., 12: "Dezembro"}:
    - MESES_PT[1]        → "Janeiro"    (chave int, como vem do banco)
    - MESES_PT.keys()    → dict_keys([1,2,...,12])
    - MESES_PT.values()  → dict_values(["Janeiro",...])
    - MESES_PT.items()   → dict_items([(1,"Janeiro"),...])
    - list(MESES_PT)     → [1, 2, ..., 12]
    - [MESES_PT[m] for m in range(1,13)] → lista completa

    Compatibilidade extra com código que usava lista 0-based:
    - MESES_PT[0]  → "Janeiro"   (fallback silencioso)
    """

    def __getitem__(self, key):
        if isinstance(key, int) and key == 0:
            # fallback 0-based → Janeiro
            return super().__getitem__(1)
        return super().__getitem__(key)


# ─── Paleta semântica ──────────────────────────────────────────────────────
CORES: dict[str, str] = {
    "positivo":   "#30D158",
    "negativo":   "#FF453A",
    "neutro":     "#8E8E93",
    "secundario": "#0A84FF",
    "estrutura":  "rgba(235,235,245,0.3)",
    "texto":      "rgba(235,235,245,0.6)",
    "bg":         "#000000",
    "surface":    "#1C1C1E",
    "borda":      "rgba(84,84,88,0.36)",
}

# ─── Paleta categórica para gráficos ──────────────────────────────────────
CORES_CAT: list[str] = [
    "#FF453A",  # vermelho
    "#0A84FF",  # azul
    "#ffa657",  # laranja
    "#ff7b72",  # coral
    "#d2a8ff",  # lilás
    "#79c0ff",  # azul claro
    "#56d364",  # verde
    "#e3b341",  # amarelo
]

# ─── Meses — dicionário 1-based (como no original) ────────────────────────
# MESES_PT[1] == "Janeiro" ... MESES_PT[12] == "Dezembro"
# Suporta .keys(), .values(), .items(), list(), len()
MESES_PT: _MesesDict = _MesesDict({
    1: "Janeiro",  2: "Fevereiro", 3: "Março",    4: "Abril",
    5: "Maio",     6: "Junho",     7: "Julho",     8: "Agosto",
    9: "Setembro", 10: "Outubro",  11: "Novembro", 12: "Dezembro",
})

# MESES_ABR — dict 1-based para consistência; também aceita indexação por lista
MESES_ABR: _MesesDict = _MesesDict({
    1: "Jan",  2: "Fev",  3: "Mar",  4: "Abr",
    5: "Mai",  6: "Jun",  7: "Jul",  8: "Ago",
    9: "Set", 10: "Out", 11: "Nov", 12: "Dez",
})

# ─── Cartões padrão ───────────────────────────────────────────────────────
CARTOES: list[str] = ["Nubank", "Inter", "Itaú", "Bradesco", "Santander",
                       "C6 Bank", "BTG", "XP", "Outro"]

CARTOES_CORES: dict[str, str] = {
    "Nubank":   "#820AD1",
    "Inter":    "#FF6B00",
    "Itaú":     "#003087",
    "Bradesco": "#CC0000",
    "Santander":"#EC0000",
    "C6 Bank":  "#2D2D2D",
    "BTG":      "#1A1A2E",
    "XP":       "#1A1A1A",
    "Outro":    "rgba(235,235,245,0.3)",
}

# ─── Formas de pagamento ───────────────────────────────────────────────────
FORMAS_PAGAMENTO: list[str] = [
    "Pix", "Boleto", "Transferência", "TED", "Cartão de Débito",
]
