from typing import Optional
from .models import TransportState

ALLOWED_TRANSITIONS = {
    TransportState.PENDING_ACCEPTANCE: [TransportState.ACCEPTED, TransportState.CANCELLED],
    TransportState.ACCEPTED: [TransportState.PICKED_UP, TransportState.CANCELLED],
    TransportState.PICKED_UP: [TransportState.IN_TRANSIT, TransportState.CANCELLED],
    TransportState.IN_TRANSIT: [TransportState.DELIVERED, TransportState.CANCELLED],
    TransportState.DELIVERED: [],
    TransportState.CANCELLED: [],
}

def is_valid_transition(current_state: Optional[str], new_state: str) -> bool:
    if current_state is None:
        return new_state == TransportState.PENDING_ACCEPTANCE.value
    try:
        current = TransportState(current_state)
        next_state = TransportState(new_state)
    except ValueError:
        return False
    allowed = ALLOWED_TRANSITIONS.get(current, [])
    return next_state in allowed

def validate_transition(current_state: Optional[str], new_state: str):
    if not is_valid_transition(current_state, new_state):
        raise ValueError(f"Transición no permitida: '{current_state}' -> '{new_state}'")