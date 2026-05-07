from dataclasses import dataclass
from typing import List, Optional


@dataclass
class AsociacionAdminViewModel:
    email: str
    nombre: str
    camara_url: Optional[str]
    rut_url: Optional[str]
    verificado: str

    @classmethod
    def from_orm(cls, a) -> "AsociacionAdminViewModel":
        return cls(
            email=a.email,
            nombre=a.nombre,
            camara_url=a.camara_url,
            rut_url=a.rut_url,
            verificado=a.verificado,
        )


@dataclass
class AdminDashboardViewModel:
    total_asociaciones: int
    total_productos: int
    total_personas: int
    total_vacantes: int
    labels_mes: List[str]
    data_mensual: List[int]
    ultimas_asociaciones: List[AsociacionAdminViewModel]
    ultimas_vacantes: List[dict]   # simple


@dataclass
class ProductoAdminViewModel:
    id: str
    nombre: str
    precio: int
    imagen_url: Optional[str]

    @classmethod
    def from_orm(cls, p) -> "ProductoAdminViewModel":
        return cls(
            id=p.id,
            nombre=p.nombre,
            precio=p.precio,
            imagen_url=p.imagen_url,
        )