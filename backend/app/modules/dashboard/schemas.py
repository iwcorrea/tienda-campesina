from pydantic import BaseModel
from typing import List, Optional

class MetricaWidget(BaseModel):
    titulo: str
    valor: int
    icono: str

class PedidoResumen(BaseModel):
    id: str
    estado: str
    comprador_email: str
    total: float
    fecha: str
    items: List[str]

class DocumentoResumen(BaseModel):
    tipo: str
    url: str
    fecha: str

class TimelineEvento(BaseModel):
    tipo: str
    descripcion: str
    fecha: str
    icono: str

class DashboardData(BaseModel):
    metricas: List[MetricaWidget]
    pedidos_recientes: List[PedidoResumen]
    timeline_pedido: Optional[List[TimelineEvento]] = None
    documentos_recientes: List[DocumentoResumen]
    notificaciones_pendientes: int