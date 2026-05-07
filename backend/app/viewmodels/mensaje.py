from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class MensajeViewModel:
    id: str
    remitente_email: str
    destinatario_email: str
    producto_id: Optional[str]
    texto: str
    leido: str
    fecha_envio: datetime
    mensaje_padre_id: Optional[str]

    @classmethod
    def from_orm(cls, mensaje) -> "MensajeViewModel":
        return cls(
            id=mensaje.id,
            remitente_email=mensaje.remitente_email,
            destinatario_email=mensaje.destinatario_email,
            producto_id=mensaje.producto_id,
            texto=mensaje.texto,
            leido=mensaje.leido,
            fecha_envio=mensaje.fecha_envio,
            mensaje_padre_id=mensaje.mensaje_padre_id,
        )