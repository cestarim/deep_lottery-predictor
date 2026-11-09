"""Significancia estadística frente al azar (sin dependencias externas).

Cada valor predicho es un ensayo de Bernoulli con p = k/N (k valores elegidos de N posibles).
Con T sorteos hay n = T*k ensayos. Dentro de un sorteo los aciertos son hipergeométricos
(varianza algo menor que la binomial), así que el test binomial es ligeramente conservador.
"""
from __future__ import annotations

import math


def binom_pvalue(k: int, n: int, p: float) -> float:
    """p-valor bilateral exacto (método de probabilidades menores o iguales)."""
    if n <= 0:
        return float("nan")
    if p <= 0 or p >= 1:
        return 1.0 if k == (0 if p <= 0 else n) else 0.0
    lg = math.lgamma
    lp, lq = math.log(p), math.log1p(-p)
    base = lg(n + 1)
    logpmf = [base - lg(i + 1) - lg(n - i + 1) + i * lp + (n - i) * lq for i in range(n + 1)]
    ref = logpmf[k] + 1e-9
    m = max(logpmf)
    total = sum(math.exp(v - m) for v in logpmf)
    tail = sum(math.exp(v - m) for v in logpmf if v <= ref)
    return min(1.0, tail / total)


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        return (float("nan"), float("nan"))
    ph = k / n
    d = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d
    h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def cohens_h(p1: float, p2: float) -> float:
    return 2 * math.asin(math.sqrt(p1)) - 2 * math.asin(math.sqrt(p2))


def summarize(hits: int, trials: int, p0: float) -> dict:
    lo, hi = wilson_ci(hits, trials)
    rate = hits / trials if trials else float("nan")
    return {
        "hits": int(hits), "trials": int(trials),
        "rate": round(rate, 5), "p0": round(p0, 5),
        "ci95": [round(lo, 5), round(hi, 5)],
        "contains_chance": bool(lo <= p0 <= hi),
        "p_value": round(binom_pvalue(hits, trials, p0), 4),
        "cohens_h": round(cohens_h(rate, p0), 4),
    }
