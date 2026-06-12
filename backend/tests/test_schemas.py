import pytest
from pydantic import ValidationError

from app.schemas.health import HealthResponse


def test_health_response_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        HealthResponse(status="ok", database="up", unexpected="value")
