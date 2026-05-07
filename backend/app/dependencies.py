from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.database import SessionLocal


def get_db():
    """Proporciona una sesión de BD por petición."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(request: Request):
    """
    Devuelve un diccionario con la información del usuario en sesión:
    {"email": "...", "tipo": "asociacion" | "comprador" | ...}
    Si no hay sesión, retorna None.
    """
    email = request.session.get("usuario")
    if not email:
        return None
    tipo = request.session.get("tipo_usuario")
    return {"email": email, "tipo": tipo}