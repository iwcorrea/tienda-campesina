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
    email = request.session.get("usuario")
    if not email:
        return None
    tipo = request.session.get("tipo_usuario")
    return {"email": email, "tipo": tipo}