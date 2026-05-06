"""utils/pdf_report.py - Relatório Financeiro One-Page v5 — layout otimizado."""
import io
from datetime import datetime
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.utils import ImageReader

MESES_PT  = {1:"Janeiro",2:"Fevereiro",3:"Março",4:"Abril",5:"Maio",6:"Junho",
              7:"Julho",8:"Agosto",9:"Setembro",10:"Outubro",11:"Novembro",12:"Dezembro"}
MESES_ABR = {1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",
              7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}

# Paleta
H_NAVY = HexColor("#0A0F1C"); H_BLUE = HexColor("#0A84FF")
H_GRN  = HexColor("#30D158"); H_RED  = HexColor("#FF453A")
H_ORG  = HexColor("#FF9F0A"); H_PRP  = HexColor("#BF5AF2")
H_DARK = HexColor("#1C1C1E"); H_GRAY = HexColor("#8E8E93")
H_LGR  = HexColor("#F5F5F7"); H_BRD  = HexColor("#E5E5EA")
H_MID  = HexColor("#2C2C2E"); H_TEAL = HexColor("#32ADE6")

M_BLUE="#0A84FF"; M_GRN="#30D158"; M_RED="#FF453A"; M_ORG="#FF9F0A"
M_PRP ="#BF5AF2"; M_GRAY="#8E8E93"; M_DARK="#1C1C1E"; M_LGR="#F5F5F7"
M_BRD ="#E5E5EA"; M_NAVY="#0A0F1C"; M_TEAL="#32ADE6"

CORES = [M_BLUE,M_GRN,M_ORG,M_RED,M_PRP,M_TEAL,"#FF375F",
         "#AC8E68","#FFD60A","#34C759","#5E5CE6"]

PW, PH = A4        # 595 x 842
MG     = 18.0      # margem lateral
CW     = PW - 2*MG # 559pt

# ── Posições Y (de baixo para cima) ──────────────────────────────────────
Y_FTR_H  = 18
Y_PARC   = Y_FTR_H + 6
Y_PARC_H = 58
Y_CART   = Y_PARC + Y_PARC_H + 8
Y_CART_H = 52
Y_LBL3   = Y_CART + Y_CART_H + 12
Y_EVOL   = Y_LBL3 + 9 + 5
Y_EVOL_H = 192
Y_LBL2   = Y_EVOL + Y_EVOL_H + 12
Y_CHRT   = Y_LBL2 + 9 + 5
Y_CHRT_H = 282
Y_LBL1   = Y_CHRT + Y_CHRT_H + 12
Y_KPI    = Y_LBL1 + 9 + 5
Y_KPI_H  = 56
Y_HDR    = Y_KPI + Y_KPI_H + 10
Y_HDR_H  = 66


def _brl(v):
    try:
        f = float(v)
        s = f"R$ {abs(f):,.2f}".replace(",","X").replace(".",",").replace("X",".")
        return f"-{s}" if f < 0 else s
    except Exception:
        return "R$ 0,00"


# ── Matplotlib charts ─────────────────────────────────────────────────────

def _mk_donut(df_cat, tot_cat, w=3.4, h=3.4):
    fig, ax = plt.subplots(figsize=(w, h), facecolor="white")
    top   = min(len(df_cat), 9)
    cats  = df_cat["categoria"].tolist()[:top]
    vals  = df_cat["valor"].astype(float).tolist()[:top]
    outr  = tot_cat - sum(vals)
    if outr > 0.5:
        cats.append("Outros"); vals.append(outr)
    cores = CORES[:len(cats)]
    wedges, _, ats = ax.pie(
        vals, labels=None,
        autopct=lambda p: f"{p:.0f}%" if p > 6 else "",
        colors=cores, startangle=90, pctdistance=0.76,
        wedgeprops=dict(width=0.46, edgecolor="white", linewidth=1.8),
    )
    for at in ats:
        at.set_fontsize(7.5); at.set_color("white"); at.set_fontweight("bold")
    ax.text(0,  0.10, _brl(tot_cat), ha="center", va="center",
            fontsize=9.5, fontweight="bold", color=M_DARK)
    ax.text(0, -0.14, "total gasto", ha="center", va="center",
            fontsize=6.5, color=M_GRAY)
    plt.tight_layout(pad=0.1)
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf, cores


# _mk_5030 substituído por _draw_5030 (canvas nativo)
def _UNUSED_mk_5030(nec_r=0, des_r=0, pou_r=0, nec_v=0, des_v=0, pou_v=0, w=3.7, h=3.7):
    return None  # função desativada

def _draw_5030(c, rx, ry, rw, rh, nec_r, des_r, pou_r, nec_v, des_v, pou_v):
    """50/30/20 desenhado 100% no canvas — zero distorção."""
    cats = [
        ("NECESSIDADES", nec_r, 50.0, nec_v, H_BLUE, HexColor("#C7E0FF")),
        ("DESEJOS",      des_r, 30.0, des_v, H_GRN,  HexColor("#C8F5D5")),
        ("POUPANÇA",     pou_r, 20.0, pou_v, H_ORG,  HexColor("#FFE5CC")),
    ]
    BAND_H  = rh / 3
    BAR_MAX = rw - 48
    RIGHT_X = rx + rw

    for i, (lbl, real, ideal, val, hcor, lcor) in enumerate(cats):
        band_bot = ry + rh - (i + 1) * BAND_H
        band_top = band_bot + BAND_H
        mid_y    = band_bot + BAND_H / 2

        # Rótulo
        c.setFillColor(hcor); c.setFont("Helvetica-Bold", 7.5)
        c.drawString(rx, band_top - 13, lbl)

        # Barra ideal (fina, clara)
        IDEAL_Y = mid_y + 2
        c.setFillColor(lcor)
        c.roundRect(rx, IDEAL_Y, BAR_MAX, 5, 1, fill=1, stroke=0)
        ideal_w = BAR_MAX * min(ideal / 100.0, 1.0)
        c.setStrokeColor(hcor); c.setLineWidth(1.0)
        c.line(rx + ideal_w, IDEAL_Y - 1, rx + ideal_w, IDEAL_Y + 6)
        c.setFillColor(H_GRAY); c.setFont("Helvetica", 5.8)
        c.drawRightString(RIGHT_X, IDEAL_Y + 1, f"Meta {ideal:.0f}%")

        # Barra real (grossa, sólida)
        REAL_Y = mid_y - 16
        c.setFillColor(H_BRD)
        c.roundRect(rx, REAL_Y, BAR_MAX, 10, 3, fill=1, stroke=0)
        real_w = max(BAR_MAX * min(real / 100.0, 1.0), 4.0) if real > 0 else 3.0
        c.setFillColor(hcor)
        c.roundRect(rx, REAL_Y, real_w, 10, 3, fill=1, stroke=0)

        c.setFillColor(H_DARK); c.setFont("Helvetica-Bold", 7)
        c.drawRightString(RIGHT_X, REAL_Y + 2, f"{real:.1f}%")

        c.setFillColor(H_GRAY); c.setFont("Helvetica", 5.8)
        c.drawString(rx, REAL_Y - 9, _brl(val))

        if i < 2:
            c.setStrokeColor(H_BRD); c.setLineWidth(0.3)
            c.line(rx, band_bot + 2, rx + rw, band_bot + 2)


def _mk_evol(df_ev, mes_atual, w=7.76, h=2.67):
    fig, ax = plt.subplots(figsize=(w, h), facecolor="white")
    x   = np.arange(12)
    rec = df_ev["rec"].tolist()
    dep = df_ev["dep"].tolist()
    sal = df_ev["sal"].tolist()
    lbls= df_ev["lbl"].tolist()

    ax.fill_between(x, rec, alpha=0.09, color=M_GRN, zorder=1)
    ax.fill_between(x, dep, alpha=0.09, color=M_RED,  zorder=1)
    ax.plot(x, rec, color=M_GRN, lw=2.2, marker="o", ms=3.8, label="Receitas",
            zorder=3, solid_capstyle="round")
    ax.plot(x, dep, color=M_RED, lw=2.2, marker="o", ms=3.8, label="Despesas",
            zorder=3, solid_capstyle="round")
    ax.plot(x, sal, color=M_BLUE, lw=1.6, marker="o", ms=3.0, label="Saldo",
            zorder=3, linestyle="--", alpha=0.85)

    mi = mes_atual - 1
    for vs, cor in [(rec,M_GRN),(dep,M_RED),(sal,M_BLUE)]:
        ax.plot(mi, vs[mi], "o", color=cor, ms=8, zorder=5,
                markeredgecolor="white", markeredgewidth=1.5)
    ax.axvline(mi, color=M_BLUE, lw=0.7, ls=":", alpha=0.45, zorder=2)

    ax.set_xticks(x)
    ax.set_xticklabels(lbls, fontsize=8, color=M_GRAY)
    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda v,_: f"R${v/1000:.0f}k" if abs(v)>=1000 else f"R${v:.0f}"))
    ax.tick_params(labelsize=8, colors=M_GRAY, left=False, bottom=False, pad=2)
    ax.spines[["top","right"]].set_visible(False)
    ax.spines[["left","bottom"]].set_color(M_BRD)
    ax.grid(axis="y", color=M_LGR, lw=0.7, zorder=0)
    ax.set_facecolor("white")
    ax.legend(fontsize=8, frameon=False, loc="upper right", ncol=3,
              handlelength=1.2, columnspacing=1.0)
    plt.tight_layout(pad=0.3)
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf


# ── Canvas helpers ────────────────────────────────────────────────────────

def _rr(c, x, y, w, h, r=4, fc=None, sc=None, lw=0.4):
    if fc: c.setFillColor(fc)
    if sc: c.setStrokeColor(sc); c.setLineWidth(lw)
    c.roundRect(x, y, w, h, r, fill=1 if fc else 0, stroke=1 if sc else 0)


def _img(c, buf, x, y, w, h):
    buf.seek(0)
    c.drawImage(ImageReader(buf), x, y, w, h, mask="auto")


def _sec(c, x, y, txt):
    c.setFillColor(H_BLUE); c.setFont("Helvetica-Bold", 7.5)
    c.drawString(x, y, txt.upper())
    tw = c.stringWidth(txt.upper(), "Helvetica-Bold", 7.5)
    c.setStrokeColor(H_BRD); c.setLineWidth(0.4)
    c.line(x + tw + 7, y + 3, x + CW, y + 3)


def _kpi(c, x, y, w, h, lbl, val, cor):
    # Fundo cinza claro
    _rr(c, x, y, w, h, r=5, fc=H_LGR, sc=H_BRD)
    # Faixa colorida no topo (sobreposta)
    c.setFillColor(cor)
    c.rect(x+0.5, y+h-5, w-1, 5, fill=1, stroke=0)
    # Label
    c.setFillColor(H_GRAY); c.setFont("Helvetica-Bold", 6)
    c.drawCentredString(x+w/2, y+h-15, lbl.upper())
    # Valor
    c.setFillColor(cor); c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(x+w/2, y + h//2 - 4, val)


def _cat_bars(c, df_cat, tot, x, y, w, h, cores):
    """Barras horizontais de categorias desenhadas no canvas."""
    if df_cat.empty:
        return
    rows  = min(len(df_cat), 8)
    ROW_H  = 18
    # Posições fixas (da direita para esquerda) — evita sobreposição
    VAL_END = x + w - 2          # borda direita do valor
    TXT_W   = 66                  # espaço reservado para "XX%  R$ 0.000,00"
    BAR_END = VAL_END - TXT_W - 4 # fim da barra track
    BAR_X   = x + 90              # início da barra (após dot + nome)
    BAR_W   = max(BAR_END - BAR_X, 20)  # largura real da barra

    for i, (_, r) in enumerate(df_cat.head(rows).iterrows()):
        ry  = y + h - (i + 1) * ROW_H
        cy  = ry + ROW_H // 2
        val = float(r["valor"])
        pct = val / tot if tot > 0 else 0
        cor = cores[i % len(cores)]

        # Zebra sutil
        if i % 2 == 0:
            c.setFillColor(HexColor("#F8F8FA"))
            c.rect(x, ry, w, ROW_H, fill=1, stroke=0)

        # Bolinha
        c.setFillColor(HexColor(cor))
        c.circle(x + 6, cy, 3, fill=1, stroke=0)

        # Nome (truncado para caber nos 90pt)
        nome = r["categoria"][:14] + "…" if len(r["categoria"]) > 14 else r["categoria"]
        c.setFillColor(H_DARK); c.setFont("Helvetica", 6.5)
        c.drawString(x + 14, cy - 2.5, nome)

        # Barra track (cinza fundo) — nunca passa de BAR_END
        bar_y = cy - 3.5
        c.setFillColor(H_BRD)
        c.roundRect(BAR_X, bar_y, BAR_W, 7, 2, fill=1, stroke=0)
        # Barra preenchida
        c.setFillColor(HexColor(cor))
        c.roundRect(BAR_X, bar_y, max(BAR_W * pct, 4), 7, 2, fill=1, stroke=0)

        # % (após barra, espaço garantido)
        c.setFillColor(H_GRAY); c.setFont("Helvetica-Bold", 6)
        c.drawString(BAR_END + 6, cy - 2.5, f"{pct*100:.0f}%")

        # Valor (alinhado à direita)
        c.setFillColor(H_DARK); c.setFont("Helvetica", 6)
        c.drawRightString(VAL_END, cy - 2.5, _brl(val))

        # Divisória
        if i < rows - 1:
            c.setStrokeColor(H_BRD); c.setLineWidth(0.15)
            c.line(x + 2, ry, x + w - 2, ry)


# ── Função principal ───────────────────────────────────────────────────────

def gerar_pdf(
    username, ano, mes,
    df_lanc, df_ganho, df_cartao_parcelas,
    df_lanc_ano, df_ganho_ano,
    cats_necessidades, cats_desejos,
):
    mes_label = MESES_PT.get(mes, str(mes))
    hoje      = datetime.now().strftime("%d/%m/%Y  %H:%M")

    # ── Cálculos ──────────────────────────────────────────────────────────
    df_deb = df_lanc[df_lanc["tipo"]=="Débito"].copy()  if not df_lanc.empty else pd.DataFrame()
    df_cre = df_lanc[df_lanc["tipo"]=="Crédito"].copy() if not df_lanc.empty else pd.DataFrame()
    g   = float(df_ganho["valor_liquido"].astype(float).sum())             if not df_ganho.empty            else 0.0
    rc  = float(df_cre["valor"].astype(float).sum())                        if not df_cre.empty              else 0.0
    dep = float(df_deb["valor"].astype(float).sum())                        if not df_deb.empty              else 0.0
    crt = float(df_cartao_parcelas["valor_parcela"].astype(float).sum())    if not df_cartao_parcelas.empty  else 0.0
    rec = g + rc
    sal = rec - dep - crt

    frames = []
    if not df_deb.empty:
        frames.append(df_deb[["categoria","valor"]].copy())
    if not df_cartao_parcelas.empty:
        frames.append(df_cartao_parcelas[["categoria","valor_parcela"]].rename(columns={"valor_parcela":"valor"}))
    df_cat = pd.DataFrame()
    if frames:
        df_cat = (pd.concat(frames, ignore_index=True)
                  .groupby("categoria")["valor"].sum()
                  .reset_index().sort_values("valor", ascending=False))
        df_cat["valor"] = df_cat["valor"].astype(float)
    tot_cat = float(df_cat["valor"].sum()) if not df_cat.empty else 0.0

    def _pct(v): return v/rec*100 if rec > 0 else 0.0
    nec_v = float(df_cat[df_cat["categoria"].isin(cats_necessidades)]["valor"].sum()) if not df_cat.empty else 0.0
    des_v = float(df_cat[df_cat["categoria"].isin(cats_desejos)]["valor"].sum())      if not df_cat.empty else 0.0
    pou_v = max(sal, 0.0)
    nec_r, des_r, pou_r = _pct(nec_v), _pct(des_v), _pct(pou_v)

    ev_rows = []
    for m in range(1,13):
        gm  = float(df_ganho_ano[df_ganho_ano["mes"]==m]["valor_liquido"].astype(float).sum()) if not df_ganho_ano.empty else 0.0
        rcm = float(df_lanc_ano[(df_lanc_ano["mes"]==m)&(df_lanc_ano["tipo"]=="Crédito")]["valor"].astype(float).sum()) if not df_lanc_ano.empty else 0.0
        dpm = float(df_lanc_ano[(df_lanc_ano["mes"]==m)&(df_lanc_ano["tipo"]=="Débito")]["valor"].astype(float).sum())  if not df_lanc_ano.empty else 0.0
        rm  = gm + rcm
        ev_rows.append({"mes":m,"lbl":MESES_ABR[m],"rec":rm,"dep":dpm,"sal":rm-dpm})
    df_ev = pd.DataFrame(ev_rows)

    # ── Charts ────────────────────────────────────────────────────────────
    donut_buf, cat_cores = (None, CORES)
    if not df_cat.empty:
        donut_buf, cat_cores = _mk_donut(df_cat, tot_cat)
        evol_buf  = _mk_evol(df_ev, mes)

    # ── Canvas ────────────────────────────────────────────────────────────
    out = io.BytesIO()
    c   = Canvas(out, pagesize=A4)

    # ══ HEADER ════════════════════════════════════════════════════════════
    c.setFillColor(H_NAVY)
    c.rect(0, Y_HDR, PW, PH - Y_HDR, fill=1, stroke=0)  # preenche até o topo
    c.setFillColor(H_BLUE)
    c.rect(0, Y_HDR, 5, Y_HDR_H, fill=1, stroke=0)     # acento vertical
    # Badge "RELATÓRIO FINANCEIRO PESSOAL" com tamanho correto
    BADGE_Y = Y_HDR + Y_HDR_H - 26   # posição do bottom do badge
    BADGE_H = 16                       # altura suficiente para o texto
    c.setFillColor(H_BLUE)
    c.roundRect(MG + 6, BADGE_Y, 158, BADGE_H, 3, fill=1, stroke=0)
    c.setFillColor(white); c.setFont("Helvetica-Bold", 7)
    c.drawString(MG + 11, BADGE_Y + 5, "RELATÓRIO FINANCEIRO PESSOAL")
    # Mês/Ano — grande
    c.setFillColor(white); c.setFont("Helvetica-Bold", 22)
    c.drawString(MG + 6, Y_HDR + 10, f"{mes_label} de {ano}")
    # Linha azul inferior
    c.setStrokeColor(H_BLUE); c.setLineWidth(1.5)
    c.line(0, Y_HDR, PW, Y_HDR)
    # Info usuário/data (direita)
    c.setFillColor(H_GRAY); c.setFont("Helvetica", 7.5)
    c.drawRightString(PW - MG, Y_HDR + Y_HDR_H - 18, f"Usuário: {username}")
    c.drawRightString(PW - MG, Y_HDR + Y_HDR_H - 30, f"Gerado em: {hoje}")

    # ══ KPI CARDS ═════════════════════════════════════════════════════════
    kgap = 7; kw = (CW - 3*kgap)/4
    kpis = [
        ("Receitas",  _brl(rec), H_GRN),
        ("Despesas",  _brl(dep), H_RED),
        ("Cartão",    _brl(crt), H_ORG),
        ("Saldo",     _brl(sal), H_GRN if sal >= 0 else H_RED),
    ]
    for i,(lbl,val,cor) in enumerate(kpis):
        _kpi(c, MG+i*(kw+kgap), Y_KPI, kw, Y_KPI_H, lbl, val, cor)

    # ══ SEÇÃO 1: DISTRIBUIÇÃO DE GASTOS ════════════════════════════════════
    _sec(c, MG, Y_LBL1, "Distribuição de Gastos")

    # Coluna esquerda: Donut + category bars
    L_W = CW * 0.48         # 268pt
    # Donut
    DONUT_SZ = 186
    donut_x = MG
    donut_y = Y_CHRT + Y_CHRT_H - DONUT_SZ
    if donut_buf:
        _img(c, donut_buf, donut_x, donut_y, DONUT_SZ, DONUT_SZ)

    # Category bars abaixo do donut
    CAT_H = Y_CHRT_H - DONUT_SZ - 6
    if CAT_H > 30 and not df_cat.empty:
        _cat_bars(c, df_cat, tot_cat,
                  donut_x, Y_CHRT, L_W, CAT_H, cat_cores)

    # Divisor vertical
    div_x = MG + L_W + 8
    c.setStrokeColor(H_BRD); c.setLineWidth(0.4)
    c.line(div_x, Y_CHRT, div_x, Y_CHRT + Y_CHRT_H)

    # Coluna direita: 50/30/20
    R_X = div_x + 8
    R_W = CW - L_W - 20
    # Card de fundo
    _rr(c, R_X-4, Y_CHRT-4, R_W+8, Y_CHRT_H+8, r=6, fc=H_LGR, sc=H_BRD)
    c.setFillColor(H_DARK); c.setFont("Helvetica-Bold", 7)
    c.drawString(R_X, Y_CHRT+Y_CHRT_H-4, "REGRA 50 / 30 / 20")
    c.setFillColor(H_GRAY); c.setFont("Helvetica", 6.5)
    c.drawString(R_X, Y_CHRT+Y_CHRT_H-14, "Meta vs. realizado (% da receita)")
    _draw_5030(c, R_X, Y_CHRT + 4, R_W, Y_CHRT_H - 22,
               nec_r, des_r, pou_r, nec_v, des_v, pou_v)

    # ══ SEÇÃO 2: EVOLUÇÃO MENSAL ════════════════════════════════════════════
    _sec(c, MG, Y_LBL2, f"Evolução Mensal — {ano}")
    _rr(c, MG-4, Y_EVOL-4, CW+8, Y_EVOL_H+8, r=6, fc=H_LGR, sc=H_BRD)
    _img(c, evol_buf, MG, Y_EVOL, CW, Y_EVOL_H)

    # ══ SEÇÃO 3: DETALHES DO CARTÃO ════════════════════════════════════════
    _sec(c, MG, Y_LBL3, "Detalhes do Cartão de Crédito")

    # KPIs do cartão
    n_parc = len(df_cartao_parcelas) if not df_cartao_parcelas.empty else 0
    n_crt  = df_cartao_parcelas["cartao"].nunique() if not df_cartao_parcelas.empty and "cartao" in df_cartao_parcelas.columns else 0
    n_vist = 0; n_prc_p = 0
    if not df_cartao_parcelas.empty and "total_parcelas" in df_cartao_parcelas.columns:
        n_vist  = int((df_cartao_parcelas["total_parcelas"].astype(int) == 1).sum())
        n_prc_p = n_parc - n_vist

    ck_gap = 7; ck_w = (CW - 3*ck_gap)/4
    ckpis = [
        ("Fatura Total", _brl(crt),                         H_ORG),
        ("Lançamentos",  f"{n_parc}",                       H_BLUE),
        ("À vista / Parc.", f"{n_vist} / {n_prc_p}",       H_PRP),
        ("Cartões",      f"{n_crt}",                        H_TEAL),
    ]
    for i,(lbl,val,cor) in enumerate(ckpis):
        _kpi(c, MG+i*(ck_w+ck_gap), Y_CART, ck_w, Y_CART_H, lbl, val, cor)

    # Mini-lista de parcelas (até 4 linhas)
    if not df_cartao_parcelas.empty:
        cols_parc = df_cartao_parcelas.columns.tolist()
        c.setFillColor(H_NAVY)
        c.roundRect(MG-4, Y_PARC-2, CW+8, Y_PARC_H+4, 6, fill=1, stroke=0)

        # Cabeçalho
        c.setFillColor(H_BLUE); c.setFont("Helvetica-Bold", 6.5)
        # Colunas com x absoluto
        COL = [MG, MG+CW*0.38, MG+CW*0.60, MG+CW*0.80]
        for htxt, cx in zip(["DESCRIÇÃO","CARTÃO","PARCELA","VALOR"], COL):
            c.drawString(cx, Y_PARC+Y_PARC_H-9, htxt)

        c.setStrokeColor(H_BLUE); c.setLineWidth(0.3)
        c.line(MG, Y_PARC+Y_PARC_H-12, MG+CW, Y_PARC+Y_PARC_H-12)

        show = df_cartao_parcelas.head(4)
        row_h2 = (Y_PARC_H - 16) / max(len(show), 1)
        for j, (_, rw) in enumerate(show.iterrows()):
            ry2 = Y_PARC + Y_PARC_H - 22 - j*row_h2
            desc = str(rw.get("descricao", "")).strip()[:28] or str(rw.get("categoria",""))[:28]
            cart = str(rw.get("cartao",""))[:14]
            pa   = rw.get("parcela_atual","-"); pt = rw.get("total_parcelas","-")
            parc_txt = f"{pa}/{pt}" if str(pa) != "-" else "—"
            val_txt  = _brl(rw.get("valor_parcela", 0))

            c.setFillColor(white); c.setFont("Helvetica", 6.5)
            c.drawString(COL[0], ry2, desc)
            c.drawString(COL[1], ry2, cart)
            c.drawString(COL[2], ry2, parc_txt)
            c.setFillColor(H_ORG)
            c.drawString(COL[3], ry2, val_txt)

            if j < len(show)-1:
                c.setStrokeColor(HexColor("#2C2C2E")); c.setLineWidth(0.2)
                c.line(MG, ry2-2, MG+CW, ry2-2)

    # ══ FOOTER ════════════════════════════════════════════════════════════
    c.setFillColor(H_NAVY)
    c.rect(0, 0, PW, Y_FTR_H, fill=1, stroke=0)
    c.setFillColor(H_GRAY); c.setFont("Helvetica", 6.5)
    c.drawCentredString(PW/2, 6, "Relatório gerado automaticamente · Finanças Pessoais")
    c.setFillColor(H_BLUE); c.setFont("Helvetica-Bold", 6.5)
    c.drawRightString(PW-MG, 6, f"{mes_label} {ano}")

    c.showPage(); c.save()
    return out.getvalue()
