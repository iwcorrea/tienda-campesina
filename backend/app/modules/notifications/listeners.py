from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.events.dispatcher import EventDispatcher
from app.modules.notifications.service import crear_notificacion

def _on_order_event(payload: BaseModel, db: Session):
    """Reacciona a cualquier evento de pedido y envía notificación."""
    # Extraemos datos según el tipo de evento
    tipo = payload.dict().get("descripcion", "")  # Podés mapear mejor según tipo_evento
    email = payload.usuario_email
    pedido_id = payload.pedido_id
    # Llamada al servicio legacy (que ya existía)
    crear_notificacion(
        db=db,
        usuario_email=email,
        tipo_evento=tipo,  # por ejemplo "order_created", "payment_confirmed"
        referencia_pedido_id=pedido_id,
        datos_extra={"estado_nuevo": payload.estado_nuevo}
    )

def register(dispatcher: EventDispatcher):
    # Registrar para todos los tipos de eventos de pedido que nos interesen
    for event_type in ["order_created", "payment_confirmed", "document_generated"]:
        dispatcher.register(event_type, _on_order_event)