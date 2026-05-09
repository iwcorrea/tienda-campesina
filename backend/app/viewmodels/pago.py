from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class PagoViewModel:
    id: str
    pedido_id: str
    comprador_email: str
    monto_total: int
    comision_plataforma: int
    monto_vendedor: int
    estado: str
    wompi_referencia: str
    fecha_creacion: Optional[datetime] = None

    @classmethod
    def from_orm(cls, pago) -> "PagoViewModel":
        return cls(
            id=pago.id,
            pedido_id=pago.pedido_id,
            comprador_email=pago.comprador_email,
            monto_total=pago.monto_total,
            comision_plataforma=pago.comision_plataforma,
            monto_vendedor=pago.monto_vendedor,
            estado=pago.estado,
            wompi_referencia=pago.wompi_referencia,
            fecha_creacion=pago.fecha_creacion,
        )