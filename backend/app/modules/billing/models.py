import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Float
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Commission(Base):
    __tablename__ = "commissions"

    id = Column(String, primary_key=True, default=generate_uuid)
    order_id = Column(String, ForeignKey("pedidos.id"), nullable=False)
    amount = Column(Integer, nullable=False)  # en COP
    percentage = Column(Float, default=5.0)
    status = Column(String, default="pending")  # pending, collected
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))