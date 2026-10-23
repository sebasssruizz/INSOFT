"""Cliente asíncrono del proveedor de IA con robustez (T3):

- Cadena de modelos de respaldo (env AI_MODEL_CHAIN, CSV, se intentan en orden).
- Reintentos con backoff exponencial + jitter y timeout configurable.
- Detección de cuota agotada (402/429) con errores tipados: la capa HTTP
  responde 503/429 estables (nunca 500 ni stacktrace).
- Circuit breaker simple: tras N fallos consecutivos se abre AntiO M segundos
  y las llamadas fallan rápido (evita martillar un proveedor caído).
"""
from __future__ import annotations

import asyncio
import random
import time
from collections import deque

import httpx

from app.core.config import settings

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterSaturatedError(Exception):
    """Cupo del límite global agotado o 429 del proveedor (respuesta 429)."""


class OpenRouterQuotaError(Exception):
    """Cuota/plan del proveedor agotado (402): respuesta controlada 503."""


class OpenRouterCallError(Exception):
    """Fallo de llamada (timeout, no 402/429, red) tras reintentos: 503."""


class _RateLimiter:
    """Rate limiter async-safe con ventana deslizante de 60 s."""

    def __init__(self, max_per_minute: int):
        self.max_per_minute = max_per_minute
        self._timestamps: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.time()
            while self._timestamps and self._timestamps[0] <= now - 60:
                self._timestamps.popleft()
            if len(self._timestamps) >= self.max_per_minute:
                wait_for = self._timestamps[0] + 60 - now
                if wait_for > 0:
                    self._lock.release()
                    try:
                        await asyncio.sleep(wait_for)
                    finally:
                        await self._lock.acquire()
                    now = time.time()
                    while self._timestamps and self._timestamps[0] <= now - 60:
                        self._timestamps.popleft()
            self._timestamps.append(time.time())


_global_limiter = _RateLimiter(settings.OPENROUTER_GLOBAL_LIMIT_PER_MIN)


class _CircuitBreaker:
    """Breaker simple por proceso: closed -> open -> (media) closed."""

    def __init__(self, threshold: int, cooldown: float):
        self.threshold = threshold
        self.cooldown = cooldown
        self._consecutive_failures = 0
        self._opened_at: float | None = None
        self._lock = asyncio.Lock()

    async def allow(self) -> bool:
        async with self._lock:
            if self._opened_at is None:
                return True
            if time.monotonic() - self._opened_at >= self.cooldown:
                # media-abierta: un intento de prueba puede pasar
                return True
            return False

    async def record_success(self) -> None:
        async with self._lock:
            self._consecutive_failures = 0
            self._opened_at = None

    async def record_failure(self) -> None:
        async with self._lock:
            self._consecutive_failures += 1
            if self._consecutive_failures >= self.threshold:
                self._opened_at = time.monotonic()


_breaker = _CircuitBreaker(settings.AI_CB_THRESHOLD, settings.AI_CB_COOLDOWN_SECS)


def _model_chain(answer_model: str) -> list[str]:
    """Cadena de modelos: AI_MODEL_CHAIN (CSV) o solo el modelo indicado."""
    raw = (settings.AI_MODEL_CHAIN or "").strip()
    chain = [m.strip() for m in raw.split(",") if m.strip()]
    if answer_model not in chain:
        chain.append(answer_model)
    return chain


def _backoff(attempt: int) -> float:
    base = max(0.05, settings.AI_BACKOFF_BASE_SECS)
    return base * (2 ** (attempt - 1)) + random.uniform(0, 0.25)


async def _post_openrouter(model: str, headers: dict, payload: dict) -> str:
    """Un ciclo completo de intentos para UN modelo (backoff + jitter)."""
    timeout = httpx.Timeout(settings.AI_TIMEOUT_SECS, connect=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(1, max(1, settings.AI_MAX_ATTEMPTS) + 1):
            try:
                resp = await client.post(OPENROUTER_URL, headers=headers, json=payload)
                if resp.status_code == 429:
                    if attempt < settings.AI_MAX_ATTEMPTS:
                        await asyncio.sleep(_backoff(attempt))
                        continue
                    raise OpenRouterSaturatedError("Rate limit 429 de OpenRouter.")
                if resp.status_code == 402:
                    raise OpenRouterQuotaError(
                        "Cuota/plan del proveedor de IA agotado (402)."
                    )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            except httpx.TimeoutException:
                if attempt < settings.AI_MAX_ATTEMPTS:
                    await asyncio.sleep(_backoff(attempt))
                    continue
                raise OpenRouterCallError(
                    f"Timeout llamando a OpenRouter ({settings.AI_TIMEOUT_SECS:.0f}s)."
                )
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status >= 500 and attempt < settings.AI_MAX_ATTEMPTS:
                    await asyncio.sleep(_backoff(attempt))
                    continue
                raise OpenRouterCallError(f"Error HTTP {status} del proveedor de IA.")
            except httpx.RequestError:
                if attempt < settings.AI_MAX_ATTEMPTS:
                    await asyncio.sleep(_backoff(attempt))
                    continue
                raise OpenRouterCallError("Error de red con el proveedor de IA.")
    raise OpenRouterCallError("La llamada al proveedor de IA falló tras reintentos.")


async def call_openrouter(
    model: str,
    system_prompt: str,
    user_content: str,
    max_tokens: int = 1200,
    temperature: float | None = None,
) -> str:
    """Llama a OpenRouter recorriendo la cadena de modelos con respaldo.

    Raises:
        OpenRouterSaturatedError: límite global o 429 del proveedor (HTTP 429).
        OpenRouterQuotaError: cuota agotada (402) — HTTP 503 con código estable.
        OpenRouterCallError: otros fallos (timeout/red/5xx) — HTTP 503.
    """
    if not settings.OPENROUTER_API_KEY:
        raise OpenRouterQuotaError(
            "Proveedor de IA no configurado (falta OPENROUTER_API_KEY)."
        )

    if not await _breaker.allow():
        raise OpenRouterCallError("Proveedor de IA en pausa (circuit breaker abierto).")

    try:
        await _global_limiter.acquire()
    except Exception as exc:
        raise OpenRouterSaturatedError("Límite global de OpenRouter alcanzado.") from exc

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    last_error: Exception | None = None
    for chain_model in _model_chain(model):
        payload = {
            "model": chain_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "max_tokens": max_tokens,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        try:
            answer = await _post_openrouter(chain_model, headers, payload)
            await _breaker.record_success()
            return answer
        except OpenRouterQuotaError as exc:
            await _breaker.record_failure()
            # 402 suele ser cuota global del proveedor: no tiene sentido pasar
            # al siguiente modelo del mismo proveedor; sale de inmediato.
            raise OpenRouterQuotaError(str(exc)) from exc
        except (OpenRouterSaturatedError, OpenRouterCallError) as exc:
            await _breaker.record_failure()
            last_error = exc
            # pasa al siguiente modelo de la cadena si existe
    raise last_error or OpenRouterCallError("Proveedor de IA no disponible.")
