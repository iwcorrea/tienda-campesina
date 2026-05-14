"""
Integración del chat con los eventos del sistema.
Cuando ocurre un evento (order_created, transport_assigned, etc.),
se puede enviar un mensaje de sistema a la sala correspondiente.
"""
from sqlalchemy.orm import Session
from app.modules.chat.service import (
    crear_room_pedido,
    añadir_transportista_a_room,
    enviar_mensaje_sistema,
)
from app.modules.chat.model import ChatRoom

def on_order_created(db: Session, pedido_id: str, usuario_email: str, **kwargs):
    """Crea la sala del pedido y envía mensaje de bienvenida."""
    room = crear_room_pedido(db, pedido_id)
    if room:
        enviar_mensaje_sistema(db, room.id, f"📝 Pedido #{pedido_id[:8]} creado. La negociación puede comenzar.")

def on_transport_assigned(db: Session, pedido_id: str, usuario_email: str, **kwargs):
    """Añade al transportista a la sala y notifica."""
    from app.models import Pedido, Transportista
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if pedido and pedido.transportista:
        transportista = db.query(Transportista).filter(Transportista.id == pedido.transportista_id).first()
        if transportista:
            añadir_transportista_a_room(db, pedido_id, transportista.email)
            room = db.query(ChatRoom).filter(ChatRoom.pedido_id == pedido_id).first()
            if room:
                enviar_mensaje_sistema(db, room.id, f"🚚 Transportista {transportista.nombre} asignado al pedido.")