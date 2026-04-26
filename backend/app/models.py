from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text
from .database import Base

class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    asociacion_email = Column(String(255), nullable=False, index=True)   # ← email de la asociación
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    precio = Column(Integer, nullable=True)
    imagen_url = Column(String(500), nullable=True)                     # URL de la imagen (por ahora manual)
    disponible = Column(Integer, default=1, nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)