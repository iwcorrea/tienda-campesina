import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Documento(Base):
    """
    Metadata de un documento generado automáticamente o manualmente.
    El archivo real (PDF, HTML) se almacena en Cloudinary.
    """
    __tablename__ = "documentos"

    id = Column(String, primary_key=True, default=generate_uuid)
    tipo = Column(String, nullable=False, index=True)          # factura, remision, etc.
    pedido_id = Column(String, ForeignKey("pedidos.id"), nullable=False, index=True)
    usuario_generador = Column(String, nullable=False)         # email de quien lo generó o "sistema"
    fecha_generacion = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    estado = Column(String, default="generado")                # generado, almacenado, entregado, anulado
    metadata_extra = Column(Text, default="")                  # JSON opcional
    storage_url = Column(Text, default="")                     # URL de Cloudinary
    version = Column(Integer, default=1)

    pedido = relationship("Pedido", backref="documentos")