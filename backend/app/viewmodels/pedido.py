from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from app.models import Pedido, ItemPedido


@dataclass
class ItemPedidoViewModel:
    producto_nombre: str
    cantidad: int
    precio_unitario: float
    subtotal: float

    @classmethod
    def from_orm(cls, item: ItemPedido) -> "ItemPedidoViewModel":
        nombre = item.producto.nombre if item.producto else "Producto eliminado"
        precio = float(item.precio_unitario_inicial) if item.precio_unitario_inicial else 0.0
        subtotal = round(item.cantidad * precio, 2)
        return cls(
            producto_nombre=nombre,
            cantidad=item.cantidad,
            precio_unitario=precio,
            subtotal=subtotal,
        )


@dataclass
class PedidoViewModel:
    id: str
    fecha: datetime
    estado: str
    total: float
    comprador_email: str
    items: List[ItemPedidoViewModel]

    @classmethod
    def from_orm(cls, pedido: Pedido) -> "PedidoViewModel":
        items_vm = [ItemPedidoViewModel.from_orm(item) for item in pedido.items]
        total = sum(item.subtotal for item in items_vm)
        return cls(
            id=pedido.id,
            fecha=pedido.fecha_creacion,
            estado=pedido.estado,
            total=total,
            comprador_email=pedido.comprador_email,
            items=items_vm,
        )