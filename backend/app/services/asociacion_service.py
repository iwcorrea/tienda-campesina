from typing import Optional
from sqlalchemy.orm import Session
from app.models import Asociacion


def obtener_asociacion_verificada_por_email(db: Session, email: str) -> Optional[Asociacion]:
    """
    Retorna la asociación con sus productos cargados (eager) si está verificada.
    """
    return (
        db.query(Asociacion)
        .filter(Asociacion.email == email, Asociacion.verificado == "1")
        .first()
    )