from pydantic import BaseModel
from typing import Optional

class OrderCreateRequest(BaseModel):
    comprador_email: str

class OrderTransitionRequest(BaseModel):
    nuevo_estado: str
    usuario_email: str = ""
    metadata: str = ""

class OrderEventResponse(BaseModel):
    id: str
    pedido_id: str
    tipo: str
    descripcion: str
    usuario_email: Optional[str]
    estado_anterior: Optional[str]
    estado_nuevo: Optional[str]
    fecha: str

    class Config:
        from_attributes = True