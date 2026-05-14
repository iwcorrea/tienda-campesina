"""
Listeners que reaccionan a eventos del sistema y ejecutan acciones en el chat.
"""
from app.modules.chat.events import on_order_created, on_transport_assigned

CHAT_EVENT_LISTENERS = {
    "order_created": on_order_created,
    "transport_assigned": on_transport_assigned,
}

def dispatch_chat_event(db, tipo_evento: str, pedido_id: str, usuario_email: str, **kwargs):
    listener = CHAT_EVENT_LISTENERS.get(tipo_evento)
    if listener:
        listener(db, pedido_id, usuario_email, **kwargs)