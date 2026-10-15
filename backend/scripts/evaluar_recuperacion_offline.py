#!/usr/bin/env python3
"""3.7 — Evaluación OFFLINE de la recuperación (RAG) del asistente.

Sin red y SIN proveedor: mide si el corpus recuperado apunta al subtema
correcto para cada pregunta del banco de pares pterigión (80 pares, archivo
NO versionado porque el repo es público; ver docs/piloto/BANCO_PARES.md).

Modo por defecto: léxico TF-IDF + coseno, 100 % local, RAM mínima.
(--embebidos queda reservado: requiere el modelo ONNX y su pico ~0.7 GB;
se documenta y se deja como paso manual posterior al import de unidad 9.)

Uso:
  python backend/scripts/evaluar_recuperacion_offline.py \
      --pares /ruta/qa_pairs_pterigion.json

Salida: docs/piloto/EVAL_RECUPERACION_OFFLINE.json + resumen en pantalla.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import time
import unicodedata
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ.parent / "docs" / "piloto" / "EVAL_RECUPERACION_OFFLINE.json"


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto.lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^a-z0-9ñ\s/]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def tokenizar(texto: str) -> list[str]:
    return [w for w in normalizar(texto).split() if len(w) > 2]


class TfIdf:
    """TF-IDF mínimo (sin dependencias externas), coseno documento consulta."""

    def __init__(self, documentos: list[str]) -> None:
        self.n = max(1, len(documentos))
        self.df: Counter[str] = Counter()
        self.tfs: list[Counter[str]] = []
        for doc in documentos:
            tf = Counter(tokenizar(doc))
            self.tfs.append(tf)
            for palabra in tf:
                self.df[palabra] += 1
        self.normas: list[float] = []
        for tf in self.tfs:
            norma = math.sqrt(
                sum((frec * math.log(self.n / (1 + self.df[palabra]))) ** 2
                    for palabra, frec in tf.items())
            )
            self.normas.append(norma or 1.0)

    def _pesos_query(self, query: str) -> dict[str, float]:
        tf = Counter(tokenizar(query))
        return {
            palabra: frec * math.log(self.n / (1 + self.df[palabra]))
            for palabra, frec in tf.items()
            if self.df.get(palabra)
        }

    def ranking(self, query: str) -> list[int]:
        pesos = self._pesos_query(query)
        norma_q = math.sqrt(sum(v * v for v in pesos.values())) or 1.0
        puntajes = []
        for i, tf in enumerate(self.tfs):
            punto = sum(peso * tf[palabra] for palabra, peso in pesos.items())
            puntajes.append(punto / (self.normas[i] * norma_q))
        orden = sorted(range(len(puntajes)), key=lambda i: -puntajes[i])
        return orden


def evaluar(pares: list[dict]) -> dict:
    subtemas = sorted({p["subtopic"] for p in pares})
    corpus_texto = {
        subte: " ".join(p["expected_answer"] for p in pares if p["subtopic"] == subte)
        for subte in subtemas
    }
    documentos = list(corpus_texto.values())
    indice = TfIdf(documentos)
    objetivo_indice = {subte: i for i, subte in enumerate(subtemas)}

    hit1 = hit3 = 0
    suma_rr = 0.0
    total_ms = 0.0
    por_subtema: dict[str, list[int]] = {s: [0, 0] for s in subtemas}
    for par in pares:
        t0 = time.time()
        orden = indice.ranking(par["question"])
        total_ms += time.time() - t0
        objetivo = objetivo_indice[par["subtopic"]]
        posicion = orden.index(objetivo) + 1 if objetivo in orden else None
        if posicion == 1:
            hit1 += 1
        if posicion is not None and posicion <= 3:
            hit3 += 1
        if posicion:
            suma_rr += 1.0 / posicion
        por_subtema[par["subtopic"]][1] += 1
        if posicion == 1:
            por_subtema[par["subtopic"]][0] += 1
    n = max(1, len(pares))
    return {
        "modo": "lexico-tfidf-coseno (100 % local, sin red)",
        "n_pares": n,
        "recall@1": round(hit1 / n, 3),
        "recall@3": round(hit3 / n, 3),
        "mrr": round(suma_rr / n, 3),
        "ms_por_consulta": round(total_ms * 1000 / n, 1),
        "por_subtema": {
            subte: {"aciertos_top1": caja[0], "total": caja[1]}
            for subte, caja in por_subtema.items()
        },
        "nota": (
            "Corpus subrogado: por subtema se concatenan las respuestas esperadas "
            "del banco. Escenario real post-import (con chunks de unidad 9 en la "
            "BD) corre de nuevo para medir contra subtopic_chunks reales."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pares", required=True, help="JSON de pares (NO versionado)")
    args = ap.parse_args()
    pares = json.loads(Path(args.pares).read_text(encoding="utf-8"))
    resultados = evaluar(pares)
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(resultados, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(resultados, indent=2, ensure_ascii=False))
    print(f"\nEscrito: {SALIDA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
