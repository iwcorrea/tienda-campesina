from sqlalchemy.orm import Session
from app.modules.orders.model import OrderEvent
from app.modules.orders.constants import EVENT_TYPES
from app.events.dispatcher import EventDispatcher
from app.events.payloads import OrderBasePayload, PaymentConfirmedPayload

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
    descripcion: str = "",
    extra: dict = None
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

    if _dispatcher:
        if tipo == "payment_confirmed" and extra:
            payload = PaymentConfirmedPayload(
                pedido_id=pedido_id,
                usuario_email=usuario_email,
                estado_anterior=estado_anterior,
                estado_nuevo=estado_nuevo,
                descripcion=descripcion,
                extra=extra,
                **extra
            )
        else:
            payload = OrderBasePayload(
                pedido_id=pedido_id,
                usuario_email=usuario_email,
                estado_anterior=estado_anterior,
                estado_nuevo=estado_nuevo,
                descripcion=descripcion,
                extra=extra or {}
            )
        _dispatcher.publish(event_type=tipo, payload=payload, db=db, origin="orders")