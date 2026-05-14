from pydantic import BaseModel
from typing import Optional

class NotificationResponse(BaseModel):
    id: str
    usuario_email: str
    tipo_evento: str
    canal: str
    estado: str
    titulo: str
    contenido: str
    referencia_pedido_id: Optional[str]
    fecha_creacion: str
    fecha_envio: Optional[str]
    fecha_lectura: Optional[str]

    class Config:
        from_attributes = True