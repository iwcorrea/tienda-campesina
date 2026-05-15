from sqlalchemy.orm import Session
from app.events.dispatcher import EventDispatcher
from app.events.payloads import OrderBasePayload, PaymentConfirmedPayload
from app.modules.chat.service import (
    crear_room_pedido,
    enviar_mensaje_sistema,
    añadir_transportista_a_room,
)

def _on_order_created(payload: OrderBasePayload, db: Session):
    """Crea la sala de chat del pedido y notifica a los participantes."""
    room = crear_room_pedido(db, payload.pedido_id)
    if room:
        enviar_mensaje_sistema(
            db,
            room.id,
            f"Pedido #{payload.pedido_id[:8]} creado."
        )

def _on_payment_confirmed(payload: PaymentConfirmedPayload, db: Session):
    """Asegura que la sala existe y notifica el pago; si hay transportista, lo añade."""
    # crear_room_pedido es idempotente: si la sala ya existe, la devuelve
    room = crear_room_pedido(db, payload.pedido_id)
    if room:
        enviar_mensaje_sistema(
            db,
            room.id,
            f"Pago confirmado por ${payload.monto_total:,}."
        )
    if payload.transportista_email:
        añadir_transportista_a_room(db, payload.pedido_id, payload.transportista_email)

def register(dispatcher: EventDispatcher):
    dispatcher.register("order_created", _on_order_created)
    dispatcher.register("payment_confirmed", _on_payment_confirmed)
    # Futuros eventos: transport_assigned, order_cancelled, etc.