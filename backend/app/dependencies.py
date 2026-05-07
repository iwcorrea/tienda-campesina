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


# ── Autenticación basada en sesión (como ya usás en main.py) ──
def get_current_user(request: Request):
    """
    Devuelve el diccionario del usuario guardado en la sesión.
    Si no hay sesión activa, devuelve None (las rutas pueden decidir si redirigir).
    """
    usuario = request.session.get("usuario")
    return usuario  # Ej: {"email": "...", "tipo": "asociacion", ...}