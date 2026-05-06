"""utils/color.py — conversão e manipulação de cores."""
from __future__ import annotations
import re


def to_rgba(color: str, alpha: float = 0.1) -> str:
    """Converte hex (#RRGGBB, #RGB, RRGGBB) ou rgba()/rgb() para rgba com alpha ajustável."""
    color = color.strip()
    if color.lower().startswith(("rgba(", "rgb(")):
        nums = re.findall(r"[\d.]+", color)
        r, g, b = int(nums[0]), int(nums[1]), int(nums[2])
        return f"rgba({r},{g},{b},{alpha})"
    h = color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        raise ValueError(f"Cor inválida: '{color}'. Use #RRGGBB, #RGB ou rgba(...).")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def hex_to_rgb(color: str) -> tuple:
    """Retorna (r, g, b) inteiros a partir de uma cor hex ou rgba."""
    color = color.strip()
    if color.lower().startswith(("rgba(", "rgb(")):
        nums = re.findall(r"[\d.]+", color)
        return int(nums[0]), int(nums[1]), int(nums[2])
    h = color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def luminance(color: str) -> float:
    """Luminância relativa WCAG (0 = preto, 1 = branco)."""
    def _lin(c: float) -> float:
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = hex_to_rgb(color)
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast_ratio(c1: str, c2: str) -> float:
    """Razão de contraste WCAG entre duas cores (mínimo 1, máximo 21)."""
    l1, l2 = luminance(c1), luminance(c2)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)
