from dataclasses import dataclass
from typing import Optional
from app.models import Transportista


@dataclass
class TransportistaViewModel:
    email: str
    nombre: str
    telefono: str
    tipo_vehiculo: str
    capacidad: str
    zona_cobertura: str
    tarifa_base: int
    costo_km: int
    documento_url: Optional[str]

    @classmethod
    def from_orm(cls, t: Transportista) -> "TransportistaViewModel":
        return cls(
            email=t.email,
            nombre=t.nombre,
            telefono=t.telefono,
            tipo_vehiculo=t.tipo_vehiculo,
            capacidad=t.capacidad,
            zona_cobertura=t.zona_cobertura,
            tarifa_base=t.tarifa_base,
            costo_km=t.costo_km,
            documento_url=t.documento_url,
        )