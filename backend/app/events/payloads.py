from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class OrderBasePayload(BaseModel):
    """Payload base para eventos de pedidos."""
    pedido_id: str
    usuario_email: str
    estado_anterior: Optional[str] = None
    estado_nuevo: Optional[str] = None
    descripcion: str = ""
    extra: Dict[str, Any] = Field(default_factory=dict)

# Podés extenderlo para otros módulos más adelante