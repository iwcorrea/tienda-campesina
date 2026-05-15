import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.orm import relationship
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class TransportState(str, Enum):
    PENDING_ACCEPTANCE = "pendiente_aceptacion"
    ACCEPTED = "aceptado"
    PICKED_UP = "recogido"
    IN_TRANSIT = "en_transito"
    DELIVERED = "entregado"
    CANCELLED = "cancelado"

class Transport(Base):
    __tablename__ = "transportes"

    id = Column(String, primary_key=True, default=generate_uuid)
    pedido_id = Column(String, ForeignKey("pedidos.id"), nullable=False, index=True)
    transportista_id = Column(String, ForeignKey("transportistas.id"), nullable=False)
    estado = Column(String, default=TransportState.PENDING_ACCEPTANCE.value)
    fecha_creacion = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    costo = Column(Integer, default=0)
    detalles = Column(JSON, default=dict)

    pedido = relationship("Pedido", backref="transportes")
    transportista = relationship("Transportista")

class TransportStateLog(Base):
    __tablename__ = "transport_state_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    transport_id = Column(String, ForeignKey("transportes.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_state = Column(String, nullable=True)
    new_state = Column(String, nullable=False)
    changed_by = Column(String, nullable=False)
    changed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    extra_data = Column(JSON, default=dict)