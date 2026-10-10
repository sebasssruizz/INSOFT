#!/usr/bin/env python3
"""Prueba de carga ligeramente (T8). NO es una herramienta de producción.

Simula N "estudiantes" concurrentes contra backend+DB DESECHABLES:
  1. login dev (DEV_AUTH_ENABLED=true),
  2. ver temario del curso General (topics + subtema),
  3. responder quiz (POST /quiz/answers idempotente por attempt),
  4. marcar progreso.

La IA se llama SOLO si el backend está con AI_MOCK=true (bloqueado en prod);
con mock no toca proveedores externos.

Uso:
  python scripts/loadtest.py --base http://localhost:8010 --users 60 --wave 10

Métricas: p50/p95 por fase, errores, y (opcional --docker-stats) uso de RAM/CPU
del contenedor backend vía docker stats.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import random
import uuid
import re
import statistics
import subprocess
import time
from dataclasses import dataclass, field

import httpx

RESULT_RE = re.compile(r"p(\d+)")


@dataclass
class Stats:
    times: list[float] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def add(self, dt: float, err: str | None):
        self.times.append(dt * 1000)
        if err:
            self.errors.append(err)

    def p(self, q) -> float:
        if not self.times:
            return 0.0
        s = sorted(self.times)
        idx = min(len(s) - 1, max(0, round(q / 100 * (len(s) + 1) - 1)))
        return s[idx]

    def summary(self, name: str):
        if not self.times:
            return f"{name}: sin datos"
        err_count = len(self.errors)
        sample = ";".join(sorted(set(self.errors)))[:180]
        return (
            f"{name}: n={len(self.times)} p50={self.p(50):.0f}ms "
            f"p95={self.p(95):.0f}ms p99={self.p(99):.0f}ms err={err_count} {sample}"
        )


async def login(client, base, correo) -> dict | None:
    r = await client.post(
        f"{base}/api/auth/dev",
        json={"email": correo, "name": correo.split("@")[0], "role": "STUDENT"},
    )
    if r.status_code != 200:
        return None
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def student_journey(client, base, user_no, stats_overall, stats_by_phase):
    cookies = httpx.Cookies()
    correo = f"loaduser{user_no}@example.com"
    headers = None
    t0 = time.perf_counter()
    for attempt in range(3):
        try:
            headers = await login(client, base, correo)
            if headers:
                break
        except Exception:
            pass
        await asyncio.sleep(0.2 * attempt)
    for phase, stat_list in [("login", stats_by_phase["login"])]:
        stat_list.add(time.perf_counter() - t0, None if headers else "login-failed")
    if not headers:
        stats_overall.add(time.perf_counter() - t0, "login")
        return

    async def req(phase, method, path, **kw):
        t = time.perf_counter()
        err = None
        try:
            r = await client.request(method, f"{base}{path}", headers=headers, timeout=30, **kw)
            if r.status_code >= 400:
                err = f"{phase}:{r.status_code}"
        except Exception as e:
            err = f"{phase}:{e.__class__.__name__}"
        dt = time.perf_counter() - t
        stats_by_phase[phase].add(dt, err)
        stats_overall.add(dt, err)
        return r

    # contenido
    r = await req("topics", "GET", "/api/courses")
    if r.status_code != 200:
        return
    courses = r.json()
    if not courses:
        return
    general = next((c for c in courses if c.get("type") == "GENERAL"), courses[0])
    r = await req("topics", "GET", f"/api/courses/{general['id']}/topics")
    if r.status_code != 200:
        return
    topic = r.json()[0]
    subtopic_id = topic["subtopics"][0]["id"]
    await req("subtopic", "GET", f"/api/subtopics/{subtopic_id}", params={"course_id": general["id"]})

    # repaso (preguntas aprobadas)
    r = await req("repaso", "GET", f"/api/topics/{topic['id']}/questions", params={"course_id": general["id"]})
    if r.status_code == 200 and r.json():
        q = r.json()[0]
        attempt = str(uuid.uuid4())
        if random.random() < 0.10:  # 10% también toca la IA (mock)
            await req("ia", "POST", "/api/ai/ask", json={"question": "¿rence del glaucoma?"})
        await req("quiz", "POST", "/api/quiz/answers", json={
            "question_id": q["id"], "selected_index": 0, "attempt_id": attempt,
        })

    await req("progreso", "POST", "/api/progress", json={
        "course_id": general["id"], "subtopic_id": subtopic_id, "completed": True,
    })


async def run(base: str, n_users: int, wave: int, docker_stats: bool) -> dict:
    stats_overall = Stats()
    phases = ["login", "topics", "subtopic", "repaso", "ia", "quiz", "progreso"]
    stats_by_phase = {p: Stats() for p in phases}
    conn = httpx.AsyncClient(limits=httpx.Limits(max_connections=wave * 2, max_keepalive_connections=wave))
    t0 = time.perf_counter()
    for i in range(0, n_users, wave):
        batch = list(range(i + 1, min(i + wave, n_users) + 1))
        await asyncio.gather(*(student_journey(conn, base, u, stats_overall, stats_by_phase) for u in batch))
        print(f"w {len(batch)} usuarios (acumulado {min(i + wave, n_users)})", flush=True)
    dt = time.perf_counter() - t0
    await conn.aclose()
    print(f"\n=== TODO: {dt:.1f}s para {n_users} usuarios ===")
    print(stats_overall.summary("TOTAL"))
    for p in phases:
        print(stats_by_phase[p].summary(p))
    result = {
        "users": n_users,
        "duration_s": round(dt, 1),
        "p50_ms": round(stats_overall.p(50), 0),
        "p95_ms": round(stats_overall.p(95), 0),
        "errors": len(stats_overall.errors),
    }
    if docker_stats:
        try:
            out = subprocess.check_output(
                ["docker", "stats", "--no-stream", "--format", "{{.Name}} {{.MemUsage}} {{.CPUPerc}}"]
            ).decode()
            result["docker"] = [
                line for line in out.splitlines() if "insoft" in line
            ]
            print("\n".join(result["docker"]))
        except Exception as e:
            print(f"(docker stats no disponible: {e})")
    print(json.dumps(result, ensure_ascii=False))
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8010")
    ap.add_argument("--users", type=int, default=30)
    ap.add_argument("--wave", type=int, default=10)
    ap.add_argument("--docker-stats", action="store_true")
    args = ap.parse_args()
    asyncio.run(run(args.base, args.users, args.wave, args.docker_stats))


if __name__ == "__main__":
    main()
