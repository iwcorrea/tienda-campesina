import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from app.modules.chat.model import ChatRoom, ChatParticipante, ChatMessage
from app.models import Pedido, ItemPedido, Producto, Transportista

def crear_room_pedido(db: Session, pedido_id: str) -> Optional[ChatRoom]:
    """Crea una sala de chat asociada a un pedido, con los participantes correctos."""
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        return None

    # Verificar si ya existe una sala para este pedido
    existente = db.query(ChatRoom).filter(ChatRoom.pedido_id == pedido_id).first()
    if existente:
        return existente

    room = ChatRoom(id=str(uuid.uuid4()), pedido_id=pedido_id, tipo="pedido")
    db.add(room)
    db.flush()

    # Añadir comprador
    db.add(ChatParticipante(id=str(uuid.uuid4()), room_id=room.id, usuario_email=pedido.comprador_email, rol="comprador"))

    # Añadir productores (asociaciones dueñas de los productos)
    asociaciones = set()
    for item in pedido.items:
        if item.producto:
            asociaciones.add(item.producto.asociacion_email)
    for email_asoc in asociaciones:
        db.add(ChatParticipante(id=str(uuid.uuid4()), room_id=room.id, usuario_email=email_asoc, rol="productor"))

    db.commit()
    db.refresh(room)
    return room

def añadir_transportista_a_room(db: Session, pedido_id: str, transportista_email: str):
    """Añade al transportista como participante de la sala del pedido."""
    room = db.query(ChatRoom).filter(ChatRoom.pedido_id == pedido_id).first()
    if not room:
        return
    existe = db.query(ChatParticipante).filter(
        ChatParticipante.room_id == room.id,
        ChatParticipante.usuario_email == transportista_email
    ).first()
    if not existe:
        db.add(ChatParticipante(id=str(uuid.uuid4()), room_id=room.id, usuario_email=transportista_email, rol="transportista"))
        db.commit()

def enviar_mensaje(db: Session, room_id: str, remitente_email: str, contenido: str, tipo: str = "texto", attachment_url: str = "") -> Optional[ChatMessage]:
    """Envía un mensaje a una sala."""
    room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not room:
        return None
    msg = ChatMessage(
        id=str(uuid.uuid4()),
        room_id=room_id,
        remitente_email=remitente_email,
        tipo=tipo,
        contenido=contenido,
        attachment_url=attachment_url,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

def enviar_mensaje_sistema(db: Session, room_id: str, contenido: str):
    """Envía un mensaje de sistema (automático) a la sala."""
    return enviar_mensaje(db, room_id, "sistema", contenido, tipo="sistema")

def obtener_mensajes_room(db: Session, room_id: str, limite: int = 50) -> List[ChatMessage]:
    return db.query(ChatMessage).filter(ChatMessage.room_id == room_id).order_by(ChatMessage.fecha_envio.asc()).limit(limite).all()

def obtener_rooms_usuario(db: Session, email: str) -> List[dict]:
    """Retorna las salas donde participa el usuario, con el último mensaje."""
    participaciones = db.query(ChatParticipante).filter(ChatParticipante.usuario_email == email).all()
    rooms = []
    for p in participaciones:
        room = p.room
        ultimo = db.query(ChatMessage).filter(ChatMessage.room_id == room.id).order_by(ChatMessage.fecha_envio.desc()).first()
        rooms.append({
            "id": room.id,
            "pedido_id": room.pedido_id,
            "tipo": room.tipo,
            "ultimo_mensaje": ultimo.contenido[:80] if ultimo else "",
            "fecha_ultimo": ultimo.fecha_envio.strftime("%d/%m %H:%M") if ultimo and ultimo.fecha_envio else "",
            "fecha_creacion": room.fecha_creacion.strftime("%d/%m/%Y") if room.fecha_creacion else "",
        })
    rooms.sort(key=lambda r: r["fecha_ultimo"], reverse=True)
    return rooms