from pydantic import ConfigDict
from pydantic.main import BaseModel


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    database: str
