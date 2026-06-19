"""DTOs del panel administrativo académico."""

from pydantic import BaseModel, ConfigDict, Field


class _Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ComisionAlumnosItem(_Schema):
    comision: str
    total: int


class ResumenAcademicoResponse(_Schema):
    total_alumnos: int
    total_calificaciones: int
    entregas_aprobadas: int
    entregas_pendientes: int
    total_materias: int
    total_carreras: int
    total_cohortes: int
    por_comision: list[ComisionAlumnosItem] = Field(default_factory=list)
