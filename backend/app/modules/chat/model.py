import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class ChatRoom(Base):
    __tablename__ = "chat_rooms"

    id = Column(String, primary_key=True, default=generate_uuid)
    pedido_id = Column(String, ForeignKey("pedidos.id"), nullable=True, index=True)
    producto_id = Column(String, ForeignKey("productos.id"), nullable=True)
    tipo = Column(String, default="pedido")  # pedido, transporte, general
    estado = Column(String, default="activa")  # activa, cerrada
    fecha_creacion = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    pedido = relationship("Pedido", backref="chat_rooms")
    participantes = relationship("ChatParticipante", back_populates="room", cascade="all, delete-orphan")
    mensajes = relationship("ChatMessage", back_populates="room", cascade="all, delete-orphan")

class ChatParticipante(Base):
    __tablename__ = "chat_participantes"

    id = Column(String, primary_key=True, default=generate_uuid)
    room_id = Column(String, ForeignKey("chat_rooms.id"), nullable=False)
    usuario_email = Column(String, nullable=False, index=True)
    rol = Column(String, default="participante")  # comprador, productor, transportista, admin
    fecha_union = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    room = relationship("ChatRoom", back_populates="participantes")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    room_id = Column(String, ForeignKey("chat_rooms.id"), nullable=False, index=True)
    remitente_email = Column(String, nullable=False)
    tipo = Column(String, default="texto")  # texto, imagen, documento, sistema
    contenido = Column(Text, default="")
    attachment_url = Column(Text, default="")
    metadata_extra = Column(Text, default="")
    fecha_envio = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    room = relationship("ChatRoom", back_populates="mensajes")