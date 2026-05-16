from sqlalchemy.orm import Session
from app.events.dispatcher import EventDispatcher
from app.events.payloads import TransportBasePayload  # o el que corresponda
from app.models import Pedido
from app.modules.billing.models import Commission
import logging

logger = logging.getLogger(__name__)

def _on_transport_delivered(payload: TransportBasePayload, db: Session):
    # Obtener el pedido asociado al transporte
    from app.models import Transport
    transport = db.query(Transport).filter(Transport.id == payload.transport_id).first()
    if not transport:
        return
    pedido = db.query(Pedido).filter(Pedido.id == transport.pedido_id).first()
    if not pedido or pedido.estado != "entregado":
        return

    # Calcular monto total del pedido (suma de items * precios acordados)
    total = 0
    for item in pedido.items:
        precio = item.precio_unitario_inicial
        for r in item.respuestas:
            if r.aceptado == "aceptado" and r.precio_contraoferta > 0:
                precio = r.precio_contraoferta
                break
        total += item.cantidad * precio

    percentage = 5.0  # Configurable
    amount = int(total * percentage / 100)

    commission = Commission(
        order_id=pedido.id,
        amount=amount,
        percentage=percentage,
    )
    db.add(commission)
    db.commit()
    logger.info(f"Comisión generada para pedido {pedido.id}: ${amount}")

def register(dispatcher: EventDispatcher):
    dispatcher.register("transport_delivered", _on_transport_delivered)