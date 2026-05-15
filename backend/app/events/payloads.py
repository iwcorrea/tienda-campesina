from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class OrderBasePayload(BaseModel):
    pedido_id: str
    usuario_email: str
    estado_anterior: Optional[str] = None
    estado_nuevo: Optional[str] = None
    descripcion: str = ""
    extra: Dict[str, Any] = Field(default_factory=dict)

class PaymentConfirmedPayload(OrderBasePayload):
    monto_total: int = 0
    comision_plataforma: int = 0
    monto_vendedor: int = 0
    vendedor_email: str = ""
    transportista_email: Optional[str] = None
    costo_envio: int = 0
    wompi_referencia: str = ""           # <-- nuevo campo