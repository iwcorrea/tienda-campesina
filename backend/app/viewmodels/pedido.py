from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from app.models import Pedido, ItemPedido

@dataclass
class DetallePedidoViewModel:
    producto_nombre: str
    cantidad: int
    precio_unitario: float
    subtotal: float
    respuestas: list

    @classmethod
    def from_orm(cls, detalle: ItemPedido) -> "DetallePedidoViewModel":
        respuestas_vm = []
        for r in detalle.respuestas:
            respuestas_vm.append({
                "aceptado": r.aceptado,
                "precio_contraoferta": r.precio_contraoferta,
                "cantidad_contraoferta": r.cantidad_contraoferta,
                "fecha_entrega_contraoferta": r.fecha_entrega_contraoferta,
                "mensaje": r.mensaje,
                "contrato_url": r.contrato_url,
                "fecha_respuesta": r.fecha_respuesta.isoformat() if r.fecha_respuesta else None
            })
        subtotal = round(detalle.cantidad * detalle.precio_unitario_inicial, 2)
        return cls(
            producto_nombre=detalle.producto.nombre if detalle.producto else "Producto eliminado",
            cantidad=detalle.cantidad,
            precio_unitario=float(detalle.precio_unitario_inicial),
            subtotal=subtotal,
            respuestas=respuestas_vm
        )

@dataclass
class PedidoViewModel:
    id: str
    fecha: datetime
    estado: str
    total: float
    comprador_email: str
    items: List[DetallePedidoViewModel]

    @classmethod
    def from_orm(cls, pedido: Pedido) -> "PedidoViewModel":
        items_vm = [DetallePedidoViewModel.from_orm(item) for item in pedido.items]
        total = sum(item.subtotal for item in items_vm)
        return cls(
            id=pedido.id,
            fecha=pedido.fecha_creacion,
            estado=pedido.estado,
            total=total,
            comprador_email=pedido.comprador_email,
            items=items_vm,
        )