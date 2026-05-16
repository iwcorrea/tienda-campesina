from fastapi import Depends, Request
from sqlalchemy.orm import Session
from app.database import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request):
    """
    Devuelve un diccionario con la información del usuario en sesión,
    incluyendo email, tipo y región.
    """
    email = request.session.get("usuario")
    if not email:
        return None
    tipo = request.session.get("tipo_usuario")
    region = request.session.get("region")      # almacenada durante el login o perfil
    return {"email": email, "tipo": tipo, "region": region}