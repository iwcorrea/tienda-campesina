from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class Asociacion(Base):
    __tablename__ = "asociaciones"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    nombre_asociacion = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    direccion = Column(String(255), nullable=True)
    telefono = Column(String(50), nullable=True)
    logo_file_id = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    fecha_registro = Column(DateTime, default=datetime.utcnow, nullable=False)

    productos = relationship("Producto", back_populates="asociacion", cascade="all, delete-orphan")


class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    asociacion_id = Column(Integer, ForeignKey("asociaciones.id"), nullable=False, index=True)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    precio = Column(Integer, nullable=True)
    imagen_file_id = Column(String(255), nullable=True)
    disponible = Column(Integer, default=1, nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)

    asociacion = relationship("Asociacion", back_populates="productos")
