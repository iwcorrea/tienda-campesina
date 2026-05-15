from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.events.dispatcher import EventDispatcher
# Importar la función original que ahora quedará como fallback
from app.modules.chat.listeners import dispatch_chat_event as original_dispatch

def _on_order_chat_event(payload: BaseModel, db: Session):
    """Cuando ocurre un evento de pedido, actualiza el chat operacional."""
    # Usamos la misma función que antes se llamaba directamente
    original_dispatch(
        db=db,
        tipo=payload.dict().get("tipo", ""),
        pedido_id=payload.pedido_id,
        usuario_email=payload.usuario_email,
        estado_nuevo=payload.estado_nuevo
    )

def register(dispatcher: EventDispatcher):
    for event_type in ["order_created", "payment_confirmed", "transport_assigned"]:
        dispatcher.register(event_type, _on_order_chat_event)