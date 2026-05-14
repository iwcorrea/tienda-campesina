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

    from app.modules.notifications.events import dispatch_event
    dispatch_event(db, tipo, pedido_id, usuario_email, **({"estado_nuevo": estado_nuevo} if estado_nuevo else {}))

    from app.modules.chat.listeners import dispatch_chat_event
    dispatch_chat_event(db, tipo, pedido_id, usuario_email, **({"estado_nuevo": estado_nuevo} if estado_nuevo else {}))