"""
Validaciones de reglas de negocio para pedidos agrícolas.
"""
from app.modules.orders.constants import VALID_TRANSITIONS, ORDER_STATES

def validar_transicion(estado_actual: str, estado_propuesto: str) -> bool:
    """Retorna True si la transición es válida."""
    if estado_actual not in VALID_TRANSITIONS:
        return False
    return estado_propuesto in VALID_TRANSITIONS[estado_actual]

def es_estado_final(estado: str) -> bool:
    """Retorna True si el pedido ya terminó su ciclo de vida."""
    return estado in ("completed", "cancelled")