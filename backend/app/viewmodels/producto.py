from __future__ import annotations

from dataclasses import dataclass

from app.models.producto import Producto


@dataclass
class ProductoViewModel:
    """Objeto plano para pasar a la plantilla, sin depender del ORM."""
    id: int
    nombre: str
    descripcion: str
    precio: float
    stock: int
    unidad_medida: str
    categoria_nombre: str
    productor_nombre: str
    imagen_url: str | None

    @classmethod
    def from_orm(cls, producto: Producto) -> ProductoViewModel:
        return cls(
            id=producto.id,
            nombre=producto.nombre,
            descripcion=producto.descripcion,
            precio=float(producto.precio),
            stock=producto.stock,
            unidad_medida=producto.unidad_medida,
            categoria_nombre=producto.categoria.nombre if producto.categoria else "",
            productor_nombre=producto.productor.nombre if producto.productor else "",
            imagen_url=producto.imagen_url,
        )