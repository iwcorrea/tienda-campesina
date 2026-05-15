from sqlalchemy.orm import Session
from app.events.dispatcher import EventDispatcher
from app.events.payloads import TransportBasePayload
from app.modules.orders.service import change_order_state
from app.modules.orders.models import OrderState
from app.models import Pedido

def _on_transport_delivered(payload: TransportBasePayload, db: Session):
    pedido = db.query(Pedido).filter(Pedido.id == payload.pedido_id).first()
    if not pedido:
        return
    try:
        change_order_state(
            db, pedido, OrderState.DELIVERED.value,
            changed_by="sistema",
            extra_data={"transport_id": payload.transport_id}
        )
        db.commit()
    except ValueError as e:
        # La transición podría no ser válida en el estado actual; lo ignoramos
        pass

def register(dispatcher: EventDispatcher):
    dispatcher.register("transport_delivered", _on_transport_delivered)