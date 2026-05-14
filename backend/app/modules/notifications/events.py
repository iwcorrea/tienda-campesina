"""
Punto de entrada para disparar notificaciones desde cualquier módulo.
Este módulo escucha los eventos del sistema (order_events) y los transforma en notificaciones.
"""
from sqlalchemy.orm import Session
from app.modules.notifications.listeners import (
    on_order_created,
    on_order_confirmed,
    on_transport_assigned,
    on_delivered,
    on_payment_confirmed,
    on_document_generated,
)

# Mapeo de tipo de evento a función listener
EVENT_LISTENERS = {
    "order_created": on_order_created,
    "order_confirmed": on_order_confirmed,
    "transport_assigned": on_transport_assigned,
    "delivered": on_delivered,
    "payment_confirmed": on_payment_confirmed,
    "document_generated": on_document_generated,
}

def dispatch_event(db: Session, tipo_evento: str, pedido_id: str, usuario_email: str, **kwargs):
    """Ejecuta el listener correspondiente al tipo de evento, si existe."""
    listener = EVENT_LISTENERS.get(tipo_evento)
    if listener:
        listener(db, pedido_id, usuario_email, **kwargs)