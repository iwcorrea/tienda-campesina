"""
Sistema de eventos de dominio para pedidos.
Cada función registra un evento en la tabla order_events.
"""
from sqlalchemy.orm import Session
from app.modules.orders.model import OrderEvent
from app.modules.orders.constants import EVENT_TYPES

def registrar_evento(
    db: Session,
    pedido_id: str,
    tipo: str,
    usuario_email: str = "",
    estado_anterior: str = None,
    estado_nuevo: str = None,
    metadata_extra: str = "",
    descripcion: str = ""
):
    """Crea un evento en el historial del pedido."""
    evento = OrderEvent(
        pedido_id=pedido_id,
        tipo=tipo,
        descripcion=descripcion or EVENT_TYPES.get(tipo, ""),
        usuario_email=usuario_email,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
        metadata_extra=metadata_extra,
    )
    db.add(evento)
    db.commit()