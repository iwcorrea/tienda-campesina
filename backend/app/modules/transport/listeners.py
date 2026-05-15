from sqlalchemy.orm import Session
from app.events.dispatcher import EventDispatcher
from app.events.payloads import PaymentConfirmedPayload
import logging

logger = logging.getLogger(__name__)

def _on_order_confirmed(payload: PaymentConfirmedPayload, db: Session):
    """
    Cuando un pedido es confirmado, se podría notificar a transportistas disponibles.
    Por ahora solo registra en log.
    """
    logger.info(f"Evento order.confirmed recibido para pedido {payload.pedido_id}. Transportistas podrían ser notificados.")

def register(dispatcher: EventDispatcher):
    dispatcher.register("order_confirmed", _on_order_confirmed)
    # Futuros: order_cancelled, etc.