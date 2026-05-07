from dataclasses import dataclass
from typing import Optional
from app.models import Producto


@dataclass
class ProductoCatalogoViewModel:
    id: str
    nombre: str
    descripcion: str
    precio: int
    imagen: str
    asociacion_email: str
    asociacion_nombre: str
    logo_url: str
    tipo: str
    tipo_precio: str
    estrellas: float
    num_valoraciones: int
    show_whatsapp: str
    telefono: str

    @classmethod
    def from_orm(
        cls,
        producto: Producto,
        promedio_estrellas: float = 0.0,
        num_valoraciones: int = 0,
    ) -> "ProductoCatalogoViewModel":
        asociacion = producto.asociacion
        return cls(
            id=producto.id,
            nombre=producto.nombre,
            descripcion=producto.descripcion,
            precio=producto.precio,
            imagen=producto.imagen_url or "https://placehold.co/300x200/5B8C51/white?text=Producto",
            asociacion_email=asociacion.email if asociacion else "",
            asociacion_nombre=asociacion.nombre if asociacion else "",
            logo_url=asociacion.logo_url if asociacion else "",
            tipo=producto.tipo,
            tipo_precio=producto.tipo_precio,
            estrellas=promedio_estrellas,
            num_valoraciones=num_valoraciones,
            show_whatsapp=asociacion.show_whatsapp if asociacion else "",
            telefono=asociacion.telefono if asociacion else "",
        )