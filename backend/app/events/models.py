import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class EventLog(Base):
    __tablename__ = "event_log"

    id = Column(String, primary_key=True, default=generate_uuid)
    event_type = Column(String, nullable=False, index=True)
    payload = Column(JSON, default=dict)
    origin = Column(String, default="")          # módulo o servicio que lo publicó
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))