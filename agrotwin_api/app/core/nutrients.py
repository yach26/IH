"""Canonical kg/ha N, P2O5 and K2O. Storage soil P/K are elemental.

FAO, Crop production levels and fertilizer use, Appendix Table 16:
https://www.fao.org/4/aq348e/aq348e.pdf
Conversions are chemical equivalents, not availability/recovery factors.
"""
from math import isfinite

P_TO_P2O5 = 2.2919
K_TO_K2O = 1.2046
CONVERSION_SOURCE = "FAO aq348e, Appendix Table 16; P×2.2919, K×1.2046"


def nutrient_value(value):
    if value is None:
        return None
    result = float(value)
    if not isfinite(result) or result < 0:
        raise ValueError("Nutrient values must be finite and nonnegative")
    return result


def normalize(n, p, k, *, p_basis="P", k_basis="K"):
    if p_basis not in ("P", "P2O5") or k_basis not in ("K", "K2O"):
        raise ValueError("Explicit P/P2O5 and K/K2O units are required")
    n, p, k = map(nutrient_value, (n, p, k))
    return {
        "N": n,
        "P2O5": None if p is None else round(p * (P_TO_P2O5 if p_basis == "P" else 1), 4),
        "K2O": None if k is None else round(k * (K_TO_K2O if k_basis == "K" else 1), 4),
    }


def elemental(p, k, *, p_basis="P", k_basis="K"):
    canonical = normalize(None, p, k, p_basis=p_basis, k_basis=k_basis)
    return (
        None if canonical["P2O5"] is None else canonical["P2O5"] / P_TO_P2O5,
        None if canonical["K2O"] is None else canonical["K2O"] / K_TO_K2O,
    )


def actionable_gap(required, soil, credits=None):
    credits = credits or dict.fromkeys(("N", "P2O5", "K2O"), 0.0)
    return {key: None if required.get(key) is None or soil.get(key) is None else
            max(0.0, round(float(required[key]) - float(soil[key]) - float(credits[key]), 1))
            for key in ("N", "P2O5", "K2O")}
