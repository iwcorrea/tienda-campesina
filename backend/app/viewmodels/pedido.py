from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List

from app.models.pedido import Pedido


@dataclass
class DetallePedidoViewModel:
    producto_nombre: str
    cantidad: int
    precio_unitario: float
    subtotal: float

    @classmethod
    def from_orm(cls, detalle) -> DetallePedidoViewModel:
        return cls(
            producto_nombre=detalle.producto.nombre if detalle.producto else "Producto eliminado",
            cantidad=detalle.cantidad,
            precio_unitario=float(detalle.precio_unitario),
            subtotal=round(detalle.cantidad * detalle.precio_unitario, 2),
        )


@dataclass
class PedidoViewModel:
    id: int
    fecha: datetime
    estado: str
    total: float
    productor_nombre: str
    comprador_nombre: str
    detalles: List[DetallePedidoViewModel]

    @classmethod
    def from_orm(cls, pedido: Pedido) -> PedidoViewModel:
        detalles_vm = [DetallePedidoViewModel.from_orm(d) for d in pedido.detalles]
        total = sum(d.subtotal for d in detalles_vm)
        return cls(
            id=pedido.id,
            fecha=pedido.fecha_creacion,
            estado=pedido.estado,
            total=total,
            productor_nombre=pedido.productor.nombre if pedido.productor else "",
            comprador_nombre=pedido.comprador.nombre if pedido.comprador else "",
            detalles=detalles_vm,
        )