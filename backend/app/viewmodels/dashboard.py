from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class ActividadViewModel:
    icono: str
    texto: str
    fecha: Optional[datetime]
    url: str


@dataclass
class DashboardViewModel:
    usuario: str
    total_productos: int
    total_valoraciones: int
    mensajes_pendientes: int
    cotizaciones_pendientes: int
    vacantes_activas: int
    favoritos_count: int
    actividades: List[ActividadViewModel]