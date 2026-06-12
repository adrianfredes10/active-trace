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

    def allow(self, key: str) -> bool:
        """Registra un intento; devuelve False si superó el límite."""
        now = time.monotonic()
        window = self._hits[key]
        while window and window[0] <= now - self.window_seconds:
            window.popleft()
        if len(window) >= self.max_attempts:
            return False
        window.append(now)
        return True

    def reset(self) -> None:
        self._hits.clear()


login_rate_limiter = RateLimiter()
