from sqlalchemy.orm import Session
from app.models import Asociacion, Persona, Transportista
import bcrypt

def autenticar_usuario(db: Session, email: str, password: str):
    """Busca al usuario en las tres tablas y devuelve (tipo, nombre, es_admin) o None."""
    # Buscar en asociaciones
    usuario = db.query(Asociacion).filter(Asociacion.email == email).first()
    if usuario:
        if bcrypt.checkpw(password.encode('utf-8'), usuario.hashed_password.encode('utf-8')):
            return ("asociacion", usuario.nombre, False)

    # Buscar en personas
    usuario = db.query(Persona).filter(Persona.email == email).first()
    if usuario:
        if bcrypt.checkpw(password.encode('utf-8'), usuario.hashed_password.encode('utf-8')):
            return ("persona", usuario.nombre, False)

    # Buscar en transportistas
    usuario = db.query(Transportista).filter(Transportista.email == email).first()
    if usuario:
        if bcrypt.checkpw(password.encode('utf-8'), usuario.hashed_password.encode('utf-8')):
            return ("transportista", usuario.nombre, False)

    # Admin hardcodeado (si aplica)
    if email == "admin@example.com" and password == "admin123":
        return ("admin", "Administrador", True)

    return None