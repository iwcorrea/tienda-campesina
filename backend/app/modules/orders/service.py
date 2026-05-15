from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import Pedido  # modelo central, permanece en app/models.py
from .models import OrderStateLog
from .validators import validate_transition
import logging

logger = logging.getLogger(__name__)

def change_order_state(
    db: Session,
    pedido: Pedido,
    new_state: str,
    changed_by: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Pedido:
    """
    Cambia el estado de un pedido validando la transición y registrando el log.
    No hace commit ni refresh (se espera que el router lo haga).
    """
    current_state = pedido.estado
    validate_transition(current_state, new_state)

    log = OrderStateLog(
        order_id=pedido.id,
        previous_state=current_state,
        new_state=new_state,
        changed_by=changed_by,
        metadata=metadata or {},
    )
    db.add(log)
    pedido.estado = new_state
    logger.info(f"Pedido {pedido.id}: '{current_state}' -> '{new_state}' por {changed_by}")
    return pedido