import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Asociacion(Base):
    __tablename__ = "asociaciones"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    nombre = Column(String)
    descripcion = Column(Text, default="")
    direccion = Column(String, default="")
    telefono = Column(String, default="")
    logo_url = Column(Text, default="")
    show_whatsapp = Column(String, default="")          # "1" o ""
    camara_url = Column(Text, default="")
    rut_url = Column(Text, default="")
    verificado = Column(String, default="")              # "1" o ""
    fecha_registro = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    productos = relationship("Producto", back_populates="asociacion", cascade="all, delete-orphan")

class Producto(Base):
    __tablename__ = "productos"

    id = Column(String, primary_key=True, default=generate_uuid)
    asociacion_email = Column(String, ForeignKey("asociaciones.email"), nullable=False, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(Text, default="")
    precio = Column(Integer, default=0)
    imagen_url = Column(Text, default="")
    tipo = Column(String, default="producto")            # "producto" o "servicio"
    tipo_precio = Column(String, default="fijo")         # "fijo" o "convenir"
    fecha_creacion = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    asociacion = relationship("Asociacion", back_populates="productos")

class Valoracion(Base):
    __tablename__ = "valoraciones"

    id = Column(String, primary_key=True, default=generate_uuid)
    producto_id = Column(String, ForeignKey("productos.id"), nullable=False)
    estrellas = Column(Integer, nullable=False)
    comentario = Column(Text, default="")
    email_usuario = Column(String, default="")
    fecha = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    producto = relationship("Producto")