"""Cliente asíncrono para OpenRouter con rate limiting global en memoria.

Controla el límite de peticiones por minuto (global, compartido por todo el
proceso del contenedor backend) para proteger el tier gratuito de OpenRouter.
"""
from __future__ import annotations

import asyncio
import time
from collections import deque

import httpx

from app.core.config import settings


class OpenRouterSaturatedError(Exception):
    """Se lanza cuando el límite global de peticiones/minuto se alcanzaría."""
    pass


class OpenRouterCallError(Exception):
    """Error en la llamada a OpenRouter (timeout, 429, 5xx, red)."""
    pass


class _RateLimiter:
    """Rate limiter thread-safe/async-safe basado en ventana deslizante de 60s."""

    def __init__(self, max_per_minute: int):
        self.max_per_minute = max_per_minute
        self._timestamps: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Bloquea hasta que haya cupo disponible en la ventana actual."""
        async with self._lock:
            now = time.time()
            # Elimina timestamps fuera de la ventana de 60s
            while self._timestamps and self._timestamps[0] <= now - 60:
                self._timestamps.popleft()

            if len(self._timestamps) >= self.max_per_minute:
                # Calcula cuánto esperar hasta que el más antiguo salga de la ventana
                wait_for = self._timestamps[0] + 60 - now
                if wait_for > 0:
                    # Libera el lock mientras esperamos
                    self._lock.release()
                    try:
                        await asyncio.sleep(wait_for)
                    finally:
                        await self._lock.acquire()
                    # Re-evalúa tras el sleep
                    now = time.time()
                    while self._timestamps and self._timestamps[0] <= now - 60:
                        self._timestamps.popleft()

            # Registra esta llamada
            self._timestamps.append(time.time())


_global_limiter = _RateLimiter(settings.OPENROUTER_GLOBAL_LIMIT_PER_MIN)


async def call_openrouter(
    model: str,
    system_prompt: str,
    user_content: str,
    max_tokens: int = 1200,
) -> str:
    """Llama a OpenRouter Chat Completions con rate limiting y reintento.

    Args:
        model: Slug del modelo en OpenRouter (ej. "liquid/lfm-2.5-2.6b:free").
        system_prompt: Prompt de sistema (rol "system").
        user_content: Contenido del usuario (rol "user").
        max_tokens: Tokens máximos de respuesta.

    Returns:
        Contenido de la respuesta (string).

    Raises:
        OpenRouterSaturatedError: Si no hay cupo en el límite global.
        OpenRouterCallError: Si la llamada falla tras reintento.
    """
    if not settings.OPENROUTER_API_KEY:
        raise OpenRouterCallError("OPENROUTER_API_KEY no configurada en el entorno.")

    # Rate limit global antes de intentar la llamada
    try:
        await _global_limiter.acquire()
    except Exception as exc:
        raise OpenRouterSaturatedError("Límite global de OpenRouter alcanzado.") from exc

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "max_tokens": max_tokens,
    }

    timeout = httpx.Timeout(20.0, connect=5.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in (1, 2):  # 1 intento + 1 reintento
            try:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 429:
                    if attempt == 1:
                        await asyncio.sleep(1.5)
                        continue
                    raise OpenRouterSaturatedError("Rate limit 429 de OpenRouter.")
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            except httpx.TimeoutException:
                if attempt == 1:
                    await asyncio.sleep(1.5)
                    continue
                raise OpenRouterCallError("Timeout llamando a OpenRouter (20s).")
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code >= 500 and attempt == 1:
                    await asyncio.sleep(1.5)
                    continue
                raise OpenRouterCallError(
                    f"Error HTTP {exc.response.status_code} de OpenRouter: {exc.response.text[:200]}"
                )
            except httpx.RequestError as exc:
                if attempt == 1:
                    await asyncio.sleep(1.5)
                    continue
                raise OpenRouterCallError(f"Error de red: {exc.__class__.__name__}")

    # No debería llegar aquí
    raise OpenRouterCallError("Llamada a OpenRouter falló tras reintento.")