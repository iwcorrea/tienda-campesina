import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Notificacion(Base):
    """
    Registro histórico de cada notificación enviada a un usuario.
    Se almacena independientemente del canal utilizado.
    """
    __tablename__ = "notificaciones"

    id = Column(String, primary_key=True, default=generate_uuid)
    usuario_email = Column(String, nullable=False, index=True)
    tipo_evento = Column(String, nullable=False)       # order_created, etc.
    canal = Column(String, default="in_app")           # in_app, email, sms, whatsapp
    estado = Column(String, default="pending")         # pending, sent, read, failed
    titulo = Column(Text, default="")
    contenido = Column(Text, default="")
    referencia_pedido_id = Column(String, nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    fecha_envio = Column(DateTime(timezone=True), nullable=True)
    fecha_lectura = Column(DateTime(timezone=True), nullable=True)