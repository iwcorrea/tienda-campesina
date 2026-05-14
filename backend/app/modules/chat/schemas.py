from pydantic import BaseModel
from typing import Optional, List

class MessageCreate(BaseModel):
    room_id: str
    contenido: str
    tipo: str = "texto"

class MessageResponse(BaseModel):
    id: str
    room_id: str
    remitente_email: str
    tipo: str
    contenido: str
    attachment_url: Optional[str]
    fecha_envio: str

    class Config:
        from_attributes = True

class RoomResponse(BaseModel):
    id: str
    pedido_id: Optional[str]
    tipo: str
    estado: str
    participantes: List[str]
    ultimo_mensaje: Optional[str]
    fecha_creacion: str