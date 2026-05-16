from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import Pedido
from .models import OrderStateLog
from .validators import validate_transition
import logging

logger = logging.getLogger(__name__)

def change_order_state(
    db: Session,
    pedido: Pedido,
    new_state: str,
    changed_by: str,
    extra_data: Optional[Dict[str, Any]] = None
) -> Pedido:
    current_state = pedido.estado

    # Idempotencia: si ya está en el estado deseado, no hacer nada
    if current_state == new_state:
        logger.info(f"Pedido {pedido.id}: estado ya es '{new_state}', cambio omitido.")
        return pedido

    validate_transition(current_state, new_state)

    log = OrderStateLog(
        order_id=pedido.id,
        previous_state=current_state,
        new_state=new_state,
        changed_by=changed_by,
        extra_data=extra_data or {},
    )
    db.add(log)
    pedido.estado = new_state
    logger.info(f"Pedido {pedido.id}: '{current_state}' -> '{new_state}' por {changed_by}")
    return pedido