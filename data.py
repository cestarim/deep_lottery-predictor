"""Carga y validación de CSV de sorteos."""
from __future__ import annotations

import io
import re
import unicodedata
from dataclasses import dataclass, field

import pandas as pd

from .games import Game


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", s.strip().lower()).strip("_")


@dataclass
class ValidationReport:
    game: str
    rows_in: int = 0
    rows_ok: int = 0
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self):
        return {
            "game": self.game,
            "ok": self.ok,
            "rows_in": self.rows_in,
            "rows_ok": self.rows_ok,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def _map_columns(df: pd.DataFrame, game: Game, report: ValidationReport) -> pd.DataFrame:
    """Renombra columnas del CSV a los nombres canónicos del juego."""
    norm = {_norm(c): c for c in df.columns}
    rename, used = {}, set()

    for alias in game.date_aliases:
        if alias in norm:
            rename[norm[alias]] = "date"
            used.add(alias)
            break
    else:
        report.errors.append(
            f"Falta la columna de fecha (se aceptan: {', '.join(game.date_aliases)})."
        )

    for g in game.groups:
        for i, canon in enumerate(g.columns(), start=1):
            candidates = [canon]
            for a in g.aliases:
                # alias con y sin guion bajo: n1, n_1, num1...
                candidates += [f"{a}_{i}", f"{a}{i}"]
                if g.count == 1:
                    candidates.append(a)
            hit = next((c for c in candidates if c in norm and norm[c] not in rename), None)
            if hit is None:
                report.errors.append(f"Falta la columna «{canon}» ({g.name}, {i}/{g.count}).")
            else:
                rename[norm[hit]] = canon
    return df.rename(columns=rename)


def validate_frame(df: pd.DataFrame, game: Game) -> tuple[pd.DataFrame, ValidationReport]:
    """Devuelve (DataFrame limpio ordenado por fecha, informe)."""
    report = ValidationReport(game=game.key, rows_in=len(df))
    if df.empty:
        report.errors.append("El CSV no contiene filas.")
        return df, report

    df = _map_columns(df, game, report)
    if report.errors:
        return df, report

    df = df[["date"] + game.all_columns()].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=False)
    for c in game.all_columns():
        df[c] = pd.to_numeric(df[c], errors="coerce")

    bad = pd.Series(False, index=df.index)
    bad_reasons: dict[str, int] = {}

    def flag(mask: pd.Series, reason: str):
        nonlocal bad
        n = int((mask & ~bad).sum())
        if n:
            bad_reasons[reason] = bad_reasons.get(reason, 0) + n
        bad |= mask

    flag(df["date"].isna(), "fecha inválida o vacía")
    for g in game.groups:
        cols = g.columns()
        flag(df[cols].isna().any(axis=1), f"valores vacíos o no numéricos en {g.name}")
        vals = df[cols]
        flag(((vals < g.low) | (vals > g.high)).any(axis=1),
             f"{g.name} fuera de rango {g.low}-{g.high}")
        flag((vals % 1 != 0).any(axis=1), f"{g.name} con decimales")
        if g.unique and g.count > 1:
            flag(vals.apply(lambda r: r.nunique() < len(cols), axis=1), f"{g.name} repetidos")

    if bad.any():
        report.warnings.append(
            f"Se descartaron {int(bad.sum())} filas: "
            + "; ".join(f"{k} ({v})" for k, v in bad_reasons.items())
        )
    df = df[~bad].copy()
    for c in game.all_columns():
        df[c] = df[c].astype(int)

    dups = int(df["date"].duplicated().sum())
    if dups:
        report.warnings.append(f"{dups} fechas duplicadas: se conserva la última de cada una.")
        df = df.drop_duplicates("date", keep="last")

    df = df.sort_values("date").reset_index(drop=True)
    report.rows_ok = len(df)
    if report.rows_ok == 0:
        report.errors.append("Ninguna fila válida tras la validación.")
    elif report.rows_ok < 100:
        report.warnings.append(
            f"Solo {report.rows_ok} sorteos válidos: insuficiente para entrenar modelos de secuencia."
        )
    return df, report


def load_csv(source, game: Game) -> tuple[pd.DataFrame, ValidationReport]:
    """Lee un CSV (ruta, bytes o file-like) detectando separador (, ; tab)."""
    if isinstance(source, (bytes, bytearray)):
        source = io.BytesIO(source)
    try:
        df = pd.read_csv(source, sep=None, engine="python", encoding="utf-8-sig")
    except Exception as e:  # CSV ilegible
        rep = ValidationReport(game=game.key)
        rep.errors.append(f"No se pudo leer el CSV: {e}")
        return pd.DataFrame(), rep
    return validate_frame(df, game)
