"""
Utilidad para construir la línea de tiempo de un pedido
a partir de sus eventos registrados en order_events.
"""
from app.modules.dashboard.widgets import widget_timeline

def obtener_timeline(db, pedido_id: str) -> list:
    return widget_timeline(db, pedido_id)