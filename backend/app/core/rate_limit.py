"""Rate limiting en memoria para endpoints sensibles (login) — C-03.

Ventana deslizante simple por clave (IP+email). Suficiente para una sola
instancia; un backend distribuido (Redis) se evalúa si escala horizontalmente.
"""

import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, max_attempts: int = 5, window_seconds: int = 60) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def _prune(self, key: str, now: float) -> deque[float]:
        window = self._hits[key]
        while window and window[0] <= now - self.window_seconds:
            window.popleft()
        return window

    def is_blocked(self, key: str) -> bool:
        """True si la clave superó el límite de fallos en la ventana."""
        now = time.monotonic()
        return len(self._prune(key, now)) >= self.max_attempts

    def record_failure(self, key: str) -> None:
        """Registra un intento fallido."""
        now = time.monotonic()
        window = self._prune(key, now)
        window.append(now)

    def clear_key(self, key: str) -> None:
        """Limpia fallos tras un login exitoso."""
        self._hits.pop(key, None)

    def allow(self, key: str) -> bool:
        """Compat tests legacy: registra fallo si no está bloqueado."""
        if self.is_blocked(key):
            return False
        self.record_failure(key)
        return True

    def reset(self) -> None:
        self._hits.clear()


login_rate_limiter = RateLimiter()
