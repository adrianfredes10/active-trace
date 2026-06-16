"""Cliente Moodle Web Services — C-09.

Errores de conectividad o respuesta inválida se mapean a MoodleUnavailable
para que el router responda 502.
"""

import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)


class MoodleUnavailable(Exception):
    """Moodle no responde o devolvió error."""


@dataclass(frozen=True)
class MoodleParticipant:
    moodle_user_id: int
    nombre: str
    apellidos: str
    email: str


class MoodleWSClient:
    def __init__(self, base_url: str, token: str, *, timeout: float = 30.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout

    async def fetch_participants(self, course_id: int) -> list[MoodleParticipant]:
        url = f"{self._base_url}/webservice/rest/server.php"
        params = {
            "wstoken": self._token,
            "wsfunction": "core_enrol_get_enrolled_users",
            "moodlewsrestformat": "json",
            "courseid": course_id,
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("moodle_ws error: %s", exc)
            raise MoodleUnavailable("Moodle no disponible") from exc

        if isinstance(payload, dict) and payload.get("exception"):
            logger.warning("moodle_ws exception: %s", payload.get("message"))
            raise MoodleUnavailable(payload.get("message", "Error Moodle"))

        if not isinstance(payload, list):
            raise MoodleUnavailable("Respuesta Moodle inválida")

        participants: list[MoodleParticipant] = []
        for row in payload:
            email = row.get("email") or ""
            if not email:
                continue
            participants.append(
                MoodleParticipant(
                    moodle_user_id=int(row["id"]),
                    nombre=row.get("firstname", ""),
                    apellidos=row.get("lastname", ""),
                    email=email,
                )
            )
        return participants
