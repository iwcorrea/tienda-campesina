from dataclasses import dataclass
from typing import List, Optional
from app.models import Producto, Asociacion


@dataclass
class ProductoPanelViewModel:
    id: str
    nombre: str
    descripcion: str
    precio: int
    imagen_url: Optional[str]
    tipo: str
    tipo_precio: str

    @classmethod
    def from_orm(cls, producto: Producto) -> "ProductoPanelViewModel":
        return cls(
            id=producto.id,
            nombre=producto.nombre,
            descripcion=producto.descripcion,
            precio=producto.precio,
            imagen_url=producto.imagen_url,
            tipo=producto.tipo,
            tipo_precio=producto.tipo_precio,
        )


@dataclass
class PanelViewModel:
    usuario: str   # nombre de la asociación
    productos: List[ProductoPanelViewModel]

    @classmethod
    def from_orm(cls, asociacion: Asociacion) -> "PanelViewModel":
        productos_vm = [ProductoPanelViewModel.from_orm(p) for p in asociacion.productos]
        return cls(
            usuario=asociacion.nombre,
            productos=productos_vm,
        )