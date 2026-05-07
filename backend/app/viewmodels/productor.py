from dataclasses import dataclass
from typing import List

from app.models.productor import Productor
from app.viewmodels.producto import ProductoViewModel  # Reutilizamos el de producto


@dataclass
class ProductorViewModel:
    id: int
    nombre: str
    descripcion: str
    ubicacion: str
    activo: bool
    total_productos: int
    productos_destacados: List[ProductoViewModel]  # Podés limitar a 4 o 5

    @classmethod
    def from_orm(cls, productor: Productor, limit_productos: int = 4) -> ProductorViewModel:
        productos = productor.productos[:limit_productos]
        productos_vm = [ProductoViewModel.from_orm(p) for p in productos]
        return cls(
            id=productor.id,
            nombre=productor.nombre,
            descripcion=productor.descripcion,
            ubicacion=f"{productor.municipio}, {productor.departamento}",
            activo=productor.activo,
            total_productos=len(productor.productos),
            productos_destacados=productos_vm,
        )