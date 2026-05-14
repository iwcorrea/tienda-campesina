import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class OrderEvent(Base):
    """
    Registro histórico de cada cambio de estado o acción relevante
    sobre un pedido. Permite trazabilidad total.
    """
    __tablename__ = "order_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    pedido_id = Column(String, ForeignKey("pedidos.id"), nullable=False, index=True)
    tipo = Column(String, nullable=False)                # ej: order_created
    descripcion = Column(Text, default="")
    usuario_email = Column(String, nullable=True)        # quién ejecutó la acción
    estado_anterior = Column(String, nullable=True)
    estado_nuevo = Column(String, nullable=True)
    metadata_extra = Column(Text, default="")            # JSON opcional para datos adicionales
    fecha = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    pedido = relationship("Pedido", backref="eventos")