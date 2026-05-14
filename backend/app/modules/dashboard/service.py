from sqlalchemy.orm import Session
from app.modules.dashboard.metrics import calcular_metricas
from app.modules.dashboard.widgets import (
    widget_pedidos_recientes,
    widget_documentos_recientes,
    widget_productos_activos,
)

def obtener_dashboard_data(db: Session, email: str, tipo_usuario: str, pedido_id: str = None) -> dict:
    """Consolida los datos necesarios para el dashboard según el tipo de usuario."""
    metricas = calcular_metricas(db, email, tipo_usuario)
    pedidos = widget_pedidos_recientes(db, email, tipo_usuario)
    productos = widget_productos_activos(db, email) if tipo_usuario == "asociacion" else []
    documentos = widget_documentos_recientes(db, pedido_id) if pedido_id else []
    timeline = None
    if pedido_id:
        timeline = widget_timeline(db, pedido_id)

    return {
        "metricas": metricas,
        "pedidos_recientes": pedidos,
        "productos_activos": productos,
        "documentos_recientes": documentos,
        "timeline": timeline,
    }