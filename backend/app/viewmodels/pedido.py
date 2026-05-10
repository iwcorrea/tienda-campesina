from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from app.models import Pedido, ItemPedido, RespuestaCotizacion
from app.utils import utc_to_colombia

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
                "factura_url": r.factura_url,
                "fecha_respuesta": utc_to_colombia(r.fecha_respuesta).isoformat() if r.fecha_respuesta else None
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
            fecha=utc_to_colombia(pedido.fecha_creacion),
            estado=pedido.estado,
            total=total,
            comprador_email=pedido.comprador_email,
            items=items_vm,
        )


@dataclass
class CotizacionEnviadaViewModel:
    """Vista detallada de un ítem solicitado por el comprador."""
    id: str
    producto_nombre: str
    producto_tipo: str
    asociacion_nombre: str
    asociacion_email: str
    pedido_id: str
    cantidad: int
    precio_unitario: float
    subtotal: float
    estado: str                         # pendiente, aceptada, pagada
    contrato_url: Optional[str]
    factura_url: Optional[str]
    fecha: datetime

    @classmethod
    def from_orm(cls, item: ItemPedido) -> "CotizacionEnviadaViewModel":
        # Determinar estado
        resp_aceptada = None
        for r in item.respuestas:
            if r.aceptado == "aceptado":
                resp_aceptada = r
                break

        if item.pedido and item.pedido.estado == "pagado":
            estado = "pagada"
        elif resp_aceptada:
            estado = "aceptada"
        else:
            estado = "pendiente"

        producto = item.producto
        asociacion = producto.asociacion if producto else None
        subtotal = item.cantidad * item.precio_unitario_inicial

        return cls(
            id=item.id,
            producto_nombre=producto.nombre if producto else "Producto eliminado",
            producto_tipo=producto.tipo if producto else "",
            asociacion_nombre=asociacion.nombre if asociacion else "",
            asociacion_email=asociacion.email if asociacion else "",
            pedido_id=item.pedido.id if item.pedido else "",
            cantidad=item.cantidad,
            precio_unitario=float(item.precio_unitario_inicial),
            subtotal=float(subtotal),
            estado=estado,
            contrato_url=resp_aceptada.contrato_url if resp_aceptada else None,
            factura_url=resp_aceptada.factura_url if resp_aceptada else None,
            fecha=utc_to_colombia(item.pedido.fecha_creacion) if item.pedido and item.pedido.fecha_creacion else None,
        )