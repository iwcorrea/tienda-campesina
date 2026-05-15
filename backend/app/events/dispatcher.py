import logging
from typing import Callable, Dict, List
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .models import EventLog
from .payloads import OrderBasePayload

logger = logging.getLogger(__name__)

ListenerType = Callable[[BaseModel, Session], None]

class EventDispatcher:
    """
    Centraliza la publicación y suscripción de eventos operacionales.
    Los módulos NUNCA se importan entre sí; solo publican/escuchan aquí.
    """
    def __init__(self):
        self._listeners: Dict[str, List[ListenerType]] = {}

    def register(self, event_type: str, listener: ListenerType):
        """Registra un listener para un tipo de evento."""
        self._listeners.setdefault(event_type, []).append(listener)
        logger.info(f"Listener registrado para evento '{event_type}': {listener.__name__}")

    def publish(self, event_type: str, payload: BaseModel, db: Session, origin: str = ""):
        """
        Publica un evento: lo guarda en event_log y llama a todos los listeners.
        """
        # Guardar en bitácora central
        log_entry = EventLog(
            event_type=event_type,
            payload=payload.dict(),
            origin=origin,
        )
        db.add(log_entry)
        db.flush()   # se hace commit en el punto de publicación (normalmente después)

        # Ejecutar listeners registrados (síncrono, dentro de la misma sesión)
        for listener in self._listeners.get(event_type, []):
            try:
                listener(payload, db)
            except Exception as e:
                logger.error(f"Error ejecutando listener {listener.__name__} para evento {event_type}: {e}")