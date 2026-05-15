import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class OrderState(str, Enum):
    # Valores que ya usa el monolito – no rompen el frontend
    DRAFT = "pendiente"
    NEGOTIATION = "aceptado"
    CONFIRMED = "pagado"
    TRANSPORT_ASSIGNED = "transporte_asignado"
    IN_TRANSIT = "en_transito"
    DELIVERED = "entregado"
    CLOSED = "cerrado"

class OrderStateLog(Base):
    __tablename__ = "order_state_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    order_id = Column(String, ForeignKey("pedidos.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_state = Column(String, nullable=True)
    new_state = Column(String, nullable=False)
    changed_by = Column(String, nullable=False)   # email o sistema
    changed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    extra_data = Column(JSON, default=dict)       # nombre no reservado