from sqlalchemy.orm import Session
from app.modules.orders.model import OrderEvent
from app.modules.orders.constants import EVENT_TYPES
from app.events.dispatcher import EventDispatcher
from app.events.payloads import OrderBasePayload

# Obtener la instancia única del dispatcher (se crea en main.py y se inyecta)
_dispatcher: EventDispatcher = None

def init_dispatcher(dispatcher: EventDispatcher):
    global _dispatcher
    _dispatcher = dispatcher

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
    # 1. Guardar el evento específico de órdenes (tabla existente)
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
    # No hacemos commit aquí, lo hará el llamante

    # 2. Publicar al EventDispatcher central
    if _dispatcher:
        payload = OrderBasePayload(
            pedido_id=pedido_id,
            usuario_email=usuario_email,
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo,
            descripcion=descripcion,
            extra={"metadata_extra": metadata_extra}
        )
        _dispatcher.publish(
            event_type=tipo,
            payload=payload,
            db=db,
            origin="orders"
        )
    else:
        # Fallback: si no se ha inicializado el dispatcher (no debería ocurrir)
        pass