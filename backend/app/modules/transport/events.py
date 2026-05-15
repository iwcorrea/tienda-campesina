from sqlalchemy.orm import Session
from app.events.dispatcher import EventDispatcher
from app.events.payloads import TransportBasePayload

_dispatcher: EventDispatcher = None

def init_dispatcher(dispatcher: EventDispatcher):
    global _dispatcher
    _dispatcher = dispatcher

def publicar_evento_transporte(
    db: Session,
    event_type: str,
    transport_id: str,
    pedido_id: str,
    usuario_email: str,
    estado_anterior: str = None,
    estado_nuevo: str = None,
    descripcion: str = "",
    extra: dict = None
):
    if _dispatcher:
        payload = TransportBasePayload(
            transport_id=transport_id,
            pedido_id=pedido_id,
            usuario_email=usuario_email,
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo,
            descripcion=descripcion,
            extra=extra or {}
        )
        _dispatcher.publish(event_type=event_type, payload=payload, db=db, origin="transport")
    else:
        # Fallback: registrar en log
        pass