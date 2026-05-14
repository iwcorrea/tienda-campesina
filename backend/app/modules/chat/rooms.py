from sqlalchemy.orm import Session
from app.modules.chat.service import crear_room_pedido

def crear_room_desde_pedido(db: Session, pedido_id: str):
    """Wrapper para crear sala desde el evento de creación de pedido."""
    return crear_room_pedido(db, pedido_id)