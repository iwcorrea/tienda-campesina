from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from .models import Transport, TransportStateLog
from .validators import validate_transition
import logging

logger = logging.getLogger(__name__)

def change_transport_state(
    db: Session,
    transport: Transport,
    new_state: str,
    changed_by: str,
    extra_data: Optional[Dict[str, Any]] = None
) -> Transport:
    current_state = transport.estado
    validate_transition(current_state, new_state)

    log = TransportStateLog(
        transport_id=transport.id,
        previous_state=current_state,
        new_state=new_state,
        changed_by=changed_by,
        extra_data=extra_data or {},
    )
    db.add(log)
    transport.estado = new_state
    logger.info(f"Transporte {transport.id}: '{current_state}' -> '{new_state}' por {changed_by}")
    return transport