#!/usr/bin/env python3
"""4.2 — Corredor de pruebas por LOTES del backend (presupuesto de RAM).

Ejecuta pytest en trozos pequeños de archivos de test (por defecto 8 por
lote), con un proceso pytest por lote: la RAM de cada lote se libera al
terminar, evitando el OOM que mató esta sesión en iteraciones anteriores.

Salidas (en backend/.pruebas/, directorio efímero):
  - junit/lote-XXX.xml    JUnit por lote (para CI)
  - log/lote-XXX.log      salida completa
  - result.json           resumen por lote
  - docs/pruebas/INFORME_BACKEND.md  informe legible

Uso:
  python backend/scripts/correr_pruebas.py               # suite completa
  python backend/scripts/correr_pruebas.py --lote 6      # lotes de 6 archivos
  python backend/scripts/correr_pruebas.py --cov         # cobertura (pytest-cov)
  python backend/scripts/correr_pruebas.py --solo "test_rag_auth.py test_db_timeouts.py"
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent  # backend/
TESTS = RAIZ / "tests"
DOCS = RAIZ.parent / "docs" / "pruebas"
SALIDA = RAIZ / ".pruebas"
# Python del venv del backend si existe: el sys.executable del llamador puede
# ser del sistema (sin pytest). El corredor usa SIEMPRE el venv del proyecto.
PYTHON = RAIZ / ".venv" / "bin" / "python"
PYTHON = str(PYTHON) if PYTHON.exists() else sys.executable


def ram_disponible_mb() -> int:
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) // 1024
    return -1


def lotes(archivos: list[str], tamanio: int) -> list[list[str]]:
    return [archivos[i : i + tamanio] for i in range(0, len(archivos), tamanio)]


def correr_lote(idx: int, archivos: list[str], con_cov: bool) -> dict:
    tag = f"lote-{idx:03d}"
    cmd = [PYTHON, "-m", "pytest", "-q", "-p", "no:randomly"]
    if con_cov:
        cmd += ["--cov=app", "--cov-append", "--cov-report=", "--cov-fail-under=0"]
    junit_dir = SALIDA / "junit"
    junit_dir.mkdir(parents=True, exist_ok=True)
    cmd += [f"--junitxml={junit_dir / tag}.xml"]
    cmd += [f"tests/{a}" for a in archivos if not a.startswith("tests/")]

    log_dir = SALIDA / "log"
    log_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    proc = subprocess.run(cmd, cwd=RAIZ, capture_output=True, text=True, timeout=3600)
    seg = round(time.time() - t0, 1)
    (log_dir / f"{tag}.log").write_text(proc.stdout + "\n" + proc.stderr, encoding="utf-8")

    resumen = "(sin resumen)"
    for line in proc.stdout.splitlines()[::-1]:
        if "passed" in line or "failed" in line or "error" in line:
            resumen = line.strip()
            break

    def num(palabra: str) -> int:
        m = re.search(rf"(\d+)\s+{palabra}", resumen)
        return int(m.group(1)) if m else 0

    return {
        "lote": tag,
        "archivos": archivos,
        "exit": proc.returncode,
        "segundos": seg,
        "passed": num("passed"),
        "failed": num("failed"),
        "error": num("error"),
        "skipped": num("skipped"),
        "ram_disponible_mb": ram_disponible_mb(),
        "resumen": resumen,
    }


def escribir_informe(resultados: list[dict], con_cov: bool) -> None:
    total = {k: sum(r[k] for r in resultados) for k in ("passed", "failed", "error", "skipped")}
    t_total = sum(r["segundos"] for r in resultados)
    filas = "\n".join(
        f"| {r['lote']} | {', '.join(r['archivos'])[:88]} | {r['passed']} | "
        f"{r['failed']} | {r['error']} | {r['segundos']} |"
        for r in resultados
    )
    cobertura = (
        "\nCobertura: ver `backend/.pruebas/cobertura.txt` (generar con: pytest --cov ... --cov-report=term-missing).\n"
        if con_cov
        else ""
    )
    doc = DOCS / "INFORME_BACKEND.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(
        "# Informe de pruebas del backend (4.2)\n\n"
        f"Generado por `backend/scripts/correr_pruebas.py` el {time.strftime('%Y-%m-%d %H:%M')}.\n"
        "Corrida por lotes (presupuesto de RAM); JUnit por lote en `backend/.pruebas/junit/`.\n\n"
        "## Resumen\n\n"
        "| pasó | falló | error | saltado | tiempo total |\n"
        "|---|---|---|---|---|\n"
        f"| {total['passed']} | {total['failed']} | {total['error']} | {total['skipped']} | {t_total:.0f} s |\n\n"
        "## Detalle por lote\n\n"
        "| lote | archivos | pasó | falló | error | s |\n"
        "|---|---|---|---|---|---|\n"
        f"{filas}\n"
        f"{cobertura}",
        encoding="utf-8",
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lote", type=int, default=8, help="archivos por lote (defecto 8)")
    ap.add_argument("--cov", action="store_true", help="cobertura con pytest-cov")
    ap.add_argument("--solo", default="", help="subset de nombres de archivos separados por espacio")
    ap.add_argument("--stop-on-fail", action="store_true", help="detener tras el primer lote fallido")
    args = ap.parse_args()

    SALIDA.mkdir(parents=True, exist_ok=True)
    lista = args.solo.split() if args.solo else sorted(p.name for p in TESTS.glob("test_*.py"))
    if args.cov:
        import shutil

        shutil.rmtree(SALIDA / "junit", ignore_errors=True)
    resultados = []
    for idx, chunk in enumerate(lotes(lista, args.lote)):
        r = correr_lote(idx, chunk, args.cov)
        resultados.append(r)
        print(
            f"{r['lote']}: {r['resumen']} ({r['segundos']} s, RAM disp. {r['ram_disponible_mb']} MB)",
            flush=True,
        )
        (SALIDA / "result.json").write_text(
            json.dumps(resultados, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        if args.stop_on_fail and (r["failed"] or r["error"]):
            break

    escribir_informe(resultados, args.cov)
    if args.cov:
        proc = subprocess.run(
            [PYTHON, "-m", "coverage", "report", "-m"], cwd=RAIZ, capture_output=True, text=True
        )
        (SALIDA / "cobertura.txt").write_text(proc.stdout, encoding="utf-8")
        proc2 = subprocess.run(
            [PYTHON, "-m", "coverage", "json", "-o", str(SALIDA / "cobertura.json")],
            cwd=RAIZ,
            capture_output=True,
            text=True,
        )
        if proc2.returncode != 0:
            print("cobertura.json no generado: " + proc2.stderr[-200:], flush=True)
        print("cobertura: " + (SALIDA / "cobertura.txt").read_text().splitlines()[-1], flush=True)
    return 1 if any(r["failed"] or r["error"] for r in resultados) else 0


if __name__ == "__main__":
    raise SystemExit(main())
