"""Recorridos de API de extremo a extremo (estudiante y docente) contra un backend en marcha.

Cada paso es una comprobación con resultado esperado. Sale con código 1 si alguno falla.
Pensado para el ensayo local tipo Neon (docs/despliegue/ENSAYO_LOCAL.md) y para cualquier
base DESECHABLE. No usa login de desarrollo: los tokens vienen de un fichero de usuarios
de prueba (scripts/ensayo_tokens.py) con permisos 600.

    python scripts/recorridos_api.py --base http://127.0.0.1:8010 --tokens FICHERO --out REPORTE.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from dataclasses import asdict, dataclass

import requests


@dataclass
class Paso:
    recorrido: str
    nombre: str
    esperado: str
    obtenido: str
    ok: bool
    ms: float


class Recorrido:
    def __init__(self, base: str, tokens: dict):
        self.base = base.rstrip("/")
        self.tokens = tokens
        self.gid: int | None = None
        self.sid: int | None = None
        self.pasos: list[Paso] = []
        self.sesion = requests.Session()

    def _auth(self, rol: str | None) -> dict:
        return {} if rol is None else {"Authorization": f"Bearer {self.tokens[rol]['token']}"}

    def llamar(self, recorrido, nombre, metodo, ruta, rol="estudiante", json_body=None, params=None):
        inicio = time.perf_counter()
        try:
            resp = self.sesion.request(
                metodo, self.base + ruta, headers=self._auth(rol), json=json_body, params=params, timeout=60,
            )
        except requests.RequestException as exc:
            self.pasos.append(Paso(recorrido, nombre, "respuesta HTTP", f"error de red: {exc.__class__.__name__}", False, 0))
            return None
        ms = (time.perf_counter() - inicio) * 1000
        return resp, ms

    def comprobar(self, recorrido, nombre, metodo, ruta, esperado_status, rol="estudiante",
                  json_body=None, params=None, extra=None):
        out = self.llamar(recorrido, nombre, metodo, ruta, rol, json_body, params)
        if out is None:
            return None
        resp, ms = out
        ok = resp.status_code == esperado_status
        if ok and extra is not None:
            try:
                ok = bool(extra(resp))
            except Exception:  # noqa: BLE001 - una verificación rota cuenta como fallo
                ok = False
        self.pasos.append(Paso(recorrido, nombre, f"HTTP {esperado_status}", f"HTTP {resp.status_code}", ok, round(ms, 1)))
        return resp

    # ── estudiante ───────────────────────────────────────────────────────────
    def recorrido_estudiante(self):
        R = "estudiante"
        self.comprobar(R, "sin token → 401", "GET", "/api/users/me", 401, rol=None)
        self.comprobar(R, "perfil propio", "GET", "/api/users/me", 200,
                       extra=lambda r: r.json()["role"] == "STUDENT")
        cursos = self.comprobar(R, "lista de cursos", "GET", "/api/courses", 200,
                                extra=lambda r: any(c["type"] == "GENERAL" for c in r.json()))
        if cursos is None:
            return
        self.gid = next(c["id"] for c in cursos.json() if c["type"] == "GENERAL")
        temas = self.comprobar(R, "unidades del curso general", "GET", f"/api/courses/{self.gid}/topics", 200,
                               extra=lambda r: len(r.json()) >= 1)
        if temas is None:
            return
        subtemas = [s for t in temas.json() for s in t["subtopics"]]
        self.sid = subtemas[0]["id"]
        sub = self.comprobar(R, "subtema con preguntas", "GET", f"/api/subtopics/{self.sid}", 200,
                             params={"course_id": self.gid},
                             extra=lambda r: "questions" in r.json())
        if sub is not None and sub.json().get("questions"):
            qid = sub.json()["questions"][0]["id"]
            self.comprobar(R, "responder pregunta (calificación en servidor)", "POST", "/api/quiz/answers", 200,
                           json_body={"question_id": qid, "selected_index": 0, "attempt_id": str(uuid.uuid4())},
                           extra=lambda r: isinstance(r.json().get("is_correct"), bool))
        self.comprobar(R, "marcar subtema completado", "POST", "/api/progress", 200,
                       json_body={"course_id": self.gid, "subtopic_id": self.sid, "completed": True})
        self.comprobar(R, "progreso del curso (subtemas)", "GET", "/api/progress/course", 200,
                       params={"course_id": self.gid},
                       extra=lambda r: r.json()["completed_subtopics"] >= 1 and r.json()["percentage"] > 0)
        self.comprobar(R, "sesión de práctica", "POST", "/api/practice/sessions", 200,
                       json_body={"subtopic_id": self.sid, "count": 3},
                       extra=lambda r: "questions" in r.json())
        self.comprobar(R, "consulta al asistente (IA simulada)", "POST", "/api/ai/ask", 200,
                       json_body={"question": "¿Qué es la córnea?", "subtopic_id": self.sid, "course_id": self.gid},
                       extra=lambda r: bool(r.json().get("respuesta")))
        self.comprobar(R, "historial del asistente", "GET", "/api/ai/history", 200)
        self.comprobar(R, "ruta de docente → 403", "GET", "/api/quiz/stats/overview", 403)

    # ── docente ──────────────────────────────────────────────────────────────
    def recorrido_docente(self):
        if self.sid is None:
            return
        R = "docente"
        curso = self.comprobar(R, "crear curso", "POST", "/api/courses", 201, rol="docente",
                               json_body={"name": "Curso de ensayo", "description": "Ensayo local"})
        if curso is None:
            return
        cid, codigo = curso.json()["id"], curso.json()["code"]
        self.comprobar(R, "estudiante se une con código", "POST", "/api/courses/join", 200,
                       json_body={"code": codigo})
        self.comprobar(R, "estudiante no puede crear curso → 403", "POST", "/api/courses", 403,
                       json_body={"name": "x", "description": ""})
        self.comprobar(R, "pregunta con 4 opciones", "POST", f"/api/content/subtopics/{self.sid}/questions", 201,
                       rol="docente",
                       json_body={"prompt": f"¿Pregunta de ensayo {uuid.uuid4().hex[:8]}?",
                                  "options": ["a", "b", "c", "d"], "correct_index": 0, "explanation": "e"})
        self.comprobar(R, "pregunta con 3 opciones → 422", "POST", f"/api/content/subtopics/{self.sid}/questions", 422,
                       rol="docente",
                       json_body={"prompt": "¿Pregunta con tres?", "options": ["a", "b", "c"], "correct_index": 0})
        gen = self.comprobar(R, "generar preguntas con IA simulada", "POST", "/api/ai/questions/generate", 201,
                             rol="docente", json_body={"subtopic_id": self.sid, "count": 2},
                             extra=lambda r: r.json()["created"] >= 1)
        if gen is not None and gen.json().get("generated"):
            pid = gen.json()["generated"][0]["id"]
            self.comprobar(R, "aprobar pregunta pendiente de IA", "POST", f"/api/content/questions/{pid}/review",
                           200, rol="docente", json_body={"action": "approve"},
                           extra=lambda r: r.json()["status"] == "approved")
        self.comprobar(R, "estadísticas de quiz", "GET", "/api/quiz/stats/overview", 200, rol="docente")
        self.comprobar(R, "exportar CSV", "GET", "/api/quiz/stats/export.csv", 200, rol="docente",
                       extra=lambda r: r.headers.get("content-type", "").startswith("text/csv"))

    # ── degradación del asistente con el proveedor caído (mock 503) ───────────
    def recorrido_degradado(self):
        if self.sid is None or self.gid is None:
            return
        R = "degradado"
        self.comprobar(R, "proveedor caído con fragmentos → 200 degradado", "POST", "/api/ai/ask", 200,
                       json_body={"question": "FALLAR consulta sobre la córnea", "subtopic_id": self.sid,
                                  "course_id": self.gid},
                       extra=lambda r: r.json().get("degraded") is True)

    def ejecutar(self) -> list[Paso]:
        self.recorrido_estudiante()
        self.recorrido_docente()
        self.recorrido_degradado()
        return self.pasos


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base", required=True)
    parser.add_argument("--tokens", required=True, help="JSON de scripts/ensayo_tokens.py")
    parser.add_argument("--out", required=True, help="reporte JSON de salida (sin tokens)")
    args = parser.parse_args()

    with open(args.tokens, encoding="utf-8") as f:
        tokens = json.load(f)
    pasos = Recorrido(args.base, tokens).ejecutar()

    total = len(pasos)
    fallos = [p for p in pasos if not p.ok]
    reporte = {
        "base": args.base,
        "total": total,
        "ok": total - len(fallos),
        "fallos": len(fallos),
        "pasos": [asdict(p) for p in pasos],
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(reporte, f, ensure_ascii=False, indent=2)
    for p in pasos:
        print(f"[{'OK ' if p.ok else 'FAIL'}] {p.recorrido:<10} {p.nombre:<46} esperado {p.esperado:<12} obtenido {p.obtenido} ({p.ms} ms)")
    print(f"\n{total - len(fallos)}/{total} pasos correctos")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
