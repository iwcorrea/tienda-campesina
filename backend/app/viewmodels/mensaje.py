from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from app.utils import utc_to_colombia

@dataclass
class MensajeChatViewModel:
    id: str
    remitente_email: str
    destinatario_email: str
    texto: str
    fecha_envio: datetime
    leido: str
    producto_id: Optional[str]
    remitente_nombre: str = ""
    destinatario_nombre: str = ""

    @classmethod
    def from_orm(cls, mensaje) -> "MensajeChatViewModel":
        return cls(
            id=mensaje.id,
            remitente_email=mensaje.remitente_email,
            destinatario_email=mensaje.destinatario_email,
            texto=mensaje.texto,
            fecha_envio=utc_to_colombia(mensaje.fecha_envio),
            leido=mensaje.leido,
            producto_id=mensaje.producto_id,
        )