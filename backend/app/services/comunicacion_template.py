"""Renderizado de plantillas de comunicación — C-12."""

import re

_VAR_PATTERN = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def render_plantilla(texto: str, variables: dict[str, str]) -> str:
    def _reemplazar(match: re.Match[str]) -> str:
        clave = match.group(1)
        return variables.get(clave, match.group(0))

    return _VAR_PATTERN.sub(_reemplazar, texto)
