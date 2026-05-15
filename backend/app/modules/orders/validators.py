from typing import Optional
from .models import OrderState

ALLOWED_TRANSITIONS = {
    OrderState.DRAFT: [OrderState.NEGOTIATION, OrderState.CLOSED],
    OrderState.NEGOTIATION: [OrderState.CONFIRMED, OrderState.DRAFT, OrderState.CLOSED],
    OrderState.CONFIRMED: [OrderState.TRANSPORT_ASSIGNED, OrderState.CLOSED],
    OrderState.TRANSPORT_ASSIGNED: [OrderState.IN_TRANSIT, OrderState.CLOSED],
    OrderState.IN_TRANSIT: [OrderState.DELIVERED, OrderState.CLOSED],
    OrderState.DELIVERED: [OrderState.CLOSED],
    OrderState.CLOSED: [],
}

def is_valid_transition(current_state: Optional[str], new_state: str) -> bool:
    if current_state is None:
        return new_state == OrderState.DRAFT.value
    try:
        current = OrderState(current_state)
        next_state = OrderState(new_state)
    except ValueError:
        return False
    allowed = ALLOWED_TRANSITIONS.get(current, [])
    return next_state in allowed

def validate_transition(current_state: Optional[str], new_state: str):
    if not is_valid_transition(current_state, new_state):
        raise ValueError(f"Transición no permitida: '{current_state}' -> '{new_state}'")