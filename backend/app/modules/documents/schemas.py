from pydantic import BaseModel
from typing import Optional

class DocumentCreateRequest(BaseModel):
    tipo: str
    pedido_id: str
    usuario_generador: str
    metadata_extra: Optional[str] = ""

class DocumentResponse(BaseModel):
    id: str
    tipo: str
    pedido_id: str
    usuario_generador: str
    fecha_generacion: str
    estado: str
    storage_url: Optional[str]
    version: int

    class Config:
        from_attributes = True