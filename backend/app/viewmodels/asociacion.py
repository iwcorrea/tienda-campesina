from dataclasses import dataclass
from typing import List
from app.models import Asociacion, Producto


@dataclass
class ProductoPerfilViewModel:
    nombre: str
    descripcion: str
    precio: int
    imagen: str
    tipo: str
    tipo_precio: str

    @classmethod
    def from_orm(cls, producto: Producto) -> "ProductoPerfilViewModel":
        return cls(
            nombre=producto.nombre,
            descripcion=producto.descripcion,
            precio=producto.precio,
            imagen=producto.imagen_url or "https://placehold.co/300x200/5B8C51/white?text=Producto",
            tipo=producto.tipo,
            tipo_precio=producto.tipo_precio,
        )


@dataclass
class AsociacionPerfilViewModel:
    email: str
    nombre: str
    descripcion: str
    direccion: str
    telefono: str
    logo_url: str
    show_whatsapp: str
    productos: List[ProductoPerfilViewModel]

    @classmethod
    def from_orm(cls, asociacion: Asociacion) -> "AsociacionPerfilViewModel":
        productos_vm = [ProductoPerfilViewModel.from_orm(p) for p in asociacion.productos]
        return cls(
            email=asociacion.email,
            nombre=asociacion.nombre,
            descripcion=asociacion.descripcion,
            direccion=asociacion.direccion,
            telefono=asociacion.telefono,
            logo_url=asociacion.logo_url,
            show_whatsapp=asociacion.show_whatsapp,
            productos=productos_vm,
        )