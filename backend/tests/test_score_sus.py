"""Score SUS del piloto (T10): corre sin red ni dependencias."""
import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def test_score_sus_calcula_promedio():
    """No importa app: es un script autónomo; ejecuta como subprocess."""
    csv_path = "/tmp/opencode/sus_test.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["respondent_id"] + [f"q{i}" for i in range(1, 11)])
        # estudiante con 5 en las positivas y 1 en las invertidas => 100
        w.writerow(["a"] + [5 if i in (1, 3, 5, 7, 9) else 1 for i in range(1, 11)])
        # neutras => 50
        w.writerow(["b"] + [3] * 10)
    out = subprocess.check_output(
        [sys.executable, str(ROOT / "scripts" / "score_sus.py"), csv_path],
        text=True,
    )
    assert "100.0" in out
    assert "50.0" in out
    assert "umbral 68" in out
