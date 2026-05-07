from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class VacanteViewModel:
    id: str
    cargo: str
    descripcion: str
    ubicacion: str
    salario: int
    tipo_contrato: str
    jornada: str
    requisitos: str
    fecha_limite: datetime
    fecha_publicacion: datetime
    terminos_url: Optional[str]
    asociacion_email: str

    @classmethod
    def from_orm(cls, vacante) -> "VacanteViewModel":
        return cls(
            id=vacante.id,
            cargo=vacante.cargo,
            descripcion=vacante.descripcion,
            ubicacion=vacante.ubicacion,
            salario=vacante.salario,
            tipo_contrato=vacante.tipo_contrato,
            jornada=vacante.jornada,
            requisitos=vacante.requisitos,
            fecha_limite=vacante.fecha_limite,
            fecha_publicacion=vacante.fecha_publicacion,
            terminos_url=vacante.terminos_url,
            asociacion_email=vacante.asociacion_email,
        )