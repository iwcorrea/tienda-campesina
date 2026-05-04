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
    show_whatsapp = Column(String, default="")
    camara_url = Column(Text, default="")
    rut_url = Column(Text, default="")
    verificado = Column(String, default="")
    fecha_registro = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    pregunta_secreta = Column(String, default="")
    respuesta_secreta_hash = Column(String, default="")

    productos = relationship("Producto", back_populates="asociacion", cascade="all, delete-orphan")
    transportistas_favoritos = relationship("TransportistaFavorito", back_populates="asociacion", cascade="all, delete-orphan")

class Producto(Base):
    __tablename__ = "productos"

    id = Column(String, primary_key=True, default=generate_uuid)
    asociacion_email = Column(String, ForeignKey("asociaciones.email"), nullable=False, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(Text, default="")
    precio = Column(Integer, default=0)
    imagen_url = Column(Text, default="")
    tipo = Column(String, default="producto")
    tipo_precio = Column(String, default="fijo")
    fecha_creacion = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    asociacion = relationship("Asociacion", back_populates="productos")
    valoraciones = relationship("Valoracion", back_populates="producto", cascade="all, delete-orphan")

class Valoracion(Base):
    __tablename__ = "valoraciones"

    id = Column(String, primary_key=True, default=generate_uuid)
    producto_id = Column(String, ForeignKey("productos.id"), nullable=False)
    estrellas = Column(Integer, nullable=False)
    comentario = Column(Text, default="")
    email_usuario = Column(String, default="")
    fecha = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    producto = relationship("Producto", back_populates="valoraciones")

class Persona(Base):
    __tablename__ = "personas"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    nombre = Column(String, nullable=False)
    telefono = Column(String, default="")
    hoja_vida_url = Column(Text, default="")
    fecha_registro = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    pregunta_secreta = Column(String, default="")
    respuesta_secreta_hash = Column(String, default="")

class Vacante(Base):
    __tablename__ = "vacantes"

    id = Column(String, primary_key=True, default=generate_uuid)
    asociacion_email = Column(String, ForeignKey("asociaciones.email"), nullable=False)
    cargo = Column(String, nullable=False)
    descripcion = Column(Text, default="")
    ubicacion = Column(String, default="")
    salario = Column(Integer, default=0)
    fecha_limite = Column(DateTime(timezone=True), nullable=False)
    fecha_publicacion = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    asociacion = relationship("Asociacion")

class Aplicacion(Base):
    __tablename__ = "aplicaciones"

    id = Column(String, primary_key=True, default=generate_uuid)
    vacante_id = Column(String, ForeignKey("vacantes.id"), nullable=False)
    persona_email = Column(String, ForeignKey("personas.email"), nullable=False)
    mensaje = Column(Text, default="")
    fecha_aplicacion = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    vacante = relationship("Vacante")
    persona = relationship("Persona")

class Configuracion(Base):
    __tablename__ = "configuracion"

    id = Column(Integer, primary_key=True, default=1)

    titulo_sitio = Column(String, default="Tienda Campesina")
    descripcion_meta = Column(Text, default="Plataforma para visibilizar asociaciones rurales.")
    google_verification = Column(String, default="")
    google_analytics_id = Column(String, default="")
    robots_txt_extra = Column(Text, default="")
    imagen_og_url = Column(Text, default="")

    color_primario = Column(String, default="#2d6a4f")
    color_secundario = Column(String, default="#1f3b2c")
    color_fondo = Column(String, default="#f8faf5")
    color_texto = Column(String, default="#2f3e2f")
    color_enlaces = Column(String, default="#2d6a4f")
    color_fondo_tarjetas = Column(String, default="#ffffff")
    color_hover = Column(String, default="#1b3324")

    fuente_nombre = Column(String, default="Nunito")
    fuente_tamano_base = Column(String, default="16px")
    fuente_url = Column(String, default="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap")

    logo_url = Column(Text, default="")
    favicon_32_url = Column(Text, default="")
    favicon_16_url = Column(Text, default="")

    css_personalizado = Column(Text, default="")

    titulo_inicio = Column(String, default="")
    descripcion_inicio = Column(String, default="")
    titulo_catalogo = Column(String, default="")
    descripcion_catalogo = Column(String, default="")
    titulo_bolsa = Column(String, default="")
    descripcion_bolsa = Column(String, default="")
    titulo_calculadora = Column(String, default="")
    descripcion_calculadora = Column(String, default="")

    inicio_titulo = Column(String, default="Asociaciones de productores campesinos")
    inicio_subtitulo = Column(Text, default="Plataforma para visibilizar asociaciones rurales, publicar productos y conectar directamente con compradores.")
    inicio_texto_tarjeta = Column(Text, default="Comparte tu historia, exhibe tus productos y fortalece la economía campesina.")
    inicio_titulo_tarjeta = Column(String, default="Impulsa tu producción local")

    footer_texto = Column(String, default="Tienda Campesina")
    footer_subtexto = Column(String, default="Apoyando la Reforma Agraria en Colombia")

    menu_mostrar_catalogo = Column(String, default="1")
    menu_mostrar_calculadora = Column(String, default="1")
    menu_mostrar_bolsa = Column(String, default="1")
    menu_enlace_extra = Column(String, default="")
    menu_url_extra = Column(String, default="")

class Mensaje(Base):
    __tablename__ = "mensajes"

    id = Column(String, primary_key=True, default=generate_uuid)
    remitente_email = Column(String, ForeignKey("asociaciones.email"), nullable=False)
    destinatario_email = Column(String, ForeignKey("asociaciones.email"), nullable=False)
    producto_id = Column(String, ForeignKey("productos.id"), nullable=True)
    texto = Column(Text, nullable=False)
    leido = Column(String, default="0")
    fecha_envio = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    mensaje_padre_id = Column(String, ForeignKey("mensajes.id"), nullable=True)

    remitente = relationship("Asociacion", foreign_keys=[remitente_email])
    destinatario = relationship("Asociacion", foreign_keys=[destinatario_email])
    producto = relationship("Producto")
    padre = relationship("Mensaje", back_populates="respuestas", remote_side=[id])
    respuestas = relationship("Mensaje", back_populates="padre", lazy="dynamic")

class Transportista(Base):
    __tablename__ = "transportistas"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    nombre = Column(String, nullable=False)
    telefono = Column(String, default="")
    tipo_vehiculo = Column(String, default="camioneta")
    capacidad = Column(String, default="500 kg")
    zona_cobertura = Column(String, default="Local")
    tarifa_base = Column(Integer, default=5000)
    costo_km = Column(Integer, default=1500)
    activo = Column(String, default="1")
    fecha_registro = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    documento_url = Column(Text, default="")

    favoritos = relationship("TransportistaFavorito", back_populates="transportista", cascade="all, delete-orphan")

class TransportistaFavorito(Base):
    __tablename__ = "transportistas_favoritos"

    id = Column(String, primary_key=True, default=generate_uuid)
    asociacion_email = Column(String, ForeignKey("asociaciones.email"), nullable=False)
    transportista_id = Column(String, ForeignKey("transportistas.id"), nullable=False)

    asociacion = relationship("Asociacion", back_populates="transportistas_favoritos")
    transportista = relationship("Transportista", back_populates="favoritos")