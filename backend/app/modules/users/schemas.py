from pydantic import BaseModel, EmailStr, validator
from typing import Optional
import re

class PerfilUpdateRequest(BaseModel):
    nombre: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    descripcion: Optional[str] = None

class SolicitudContactoRequest(BaseModel):
    contacto_email: str

class MensajeRequest(BaseModel):
    texto: str
    destinatario_email: str
    producto_id: Optional[str] = None