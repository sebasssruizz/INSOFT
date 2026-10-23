#!/usr/bin/env python3
"""Puntaje SUS de la encuesta de usabilidad (T10).

Lee un CSV con columnas respondent_id y q1..q10 (escalas 1-5, invertidas las
posiciones 2,4,6,8,10). Imprime el score SUS 0-100 por respondiente y el
promedio. Cumple con la práctica estándar SUS (Baseline leve).

Uso:
    python scripts/score_sus.py [archivo.csv]
"""
import csv
import sys
from pathlib import Path

REVERSED = {2, 4, 6, 8, 10}


def load(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        raise SystemExit(f"{path}: sin filas")
    return rows


def sus_score(row: dict) -> float:
    """SUS estándar: positivo (v-1), invertido (5-v); 10 ítems 0-4; ∑ × 2.5."""
    total = 0
    for i in range(1, 11):
        raw = row.get(f"q{i}") or row.get(f"Q{i}")
        if raw is None or str(raw).strip() == "":
            raise SystemExit(f"Columna q{i} faltante en {row.get('respondent_id', '?')}")
        value = max(1, min(5, int(float(str(raw).strip()))))
        total += (value - 1) if i not in REVERSED else (5 - value)
    return total * 2.5  # 0..100


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else "respuestas.csv"
    if not Path(path).exists():
        raise SystemExit(f"No existe {path}")
    rows = load(path)
    scores = [sus_score(r) for r in rows]
    for row, score in zip(rows, scores):
        ident = row.get("respondent_id", "?")
        print(f"{ident}: {score:.1f}")
    avg = sum(scores) / len(scores)
    print(f"\nn={len(rows)} SUS promedio = {avg:.1f} / 100 "
          f"({'por encima' if avg >= 68 else 'BAJO'} del umbral 68)")


if __name__ == "__main__":
    main()
