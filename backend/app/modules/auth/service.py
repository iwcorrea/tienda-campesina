import re
import time
import bcrypt
from sqlalchemy.orm import Session
from app.models import Asociacion, Persona, Transportista

def validar_contraseña(password: str):
    if len(password) < 12:
        return False, "La contraseña debe tener al menos 12 caracteres."
    if not re.search(r'[A-Z]', password):
        return False, "Debe incluir al menos una letra mayúscula."
    if not re.search(r'[a-z]', password):
        return False, "Debe incluir al menos una letra minúscula."
    if not re.search(r'[0-9]', password):
        return False, "Debe incluir al menos un número."
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>/?\\|`~]', password):
        return False, "Debe incluir al menos un símbolo especial."
    return True, ""

def autenticar_usuario(db: Session, email: str, password: str):
    """Retorna (tipo, nombre, es_admin) o None si falla."""
    asociacion = db.query(Asociacion).filter(Asociacion.email == email).first()
    if asociacion and bcrypt.checkpw(password.encode(), asociacion.hashed_password.encode()):
        return "asociacion", asociacion.nombre or email, email == "admin@example.com"
    persona = db.query(Persona).filter(Persona.email == email).first()
    if persona and bcrypt.checkpw(password.encode(), persona.hashed_password.encode()):
        return "persona", persona.nombre or email, False
    transportista = db.query(Transportista).filter(Transportista.email == email).first()
    if transportista and bcrypt.checkpw(password.encode(), transportista.hashed_password.encode()):
        return "transportista", transportista.nombre or email, False
    return None

def registrar_usuario(db: Session, tipo: str, datos: dict):
    """Registra un nuevo usuario. Retorna True si fue exitoso, o un mensaje de error."""
    hashed = bcrypt.hashpw(datos["password"].encode(), bcrypt.gensalt()).decode()
    if tipo == "asociacion":
        if db.query(Asociacion).filter(Asociacion.email == datos["email"]).first():
            return "Ya existe una asociación con ese correo."
        db.add(Asociacion(
            email=datos["email"],
            hashed_password=hashed,
            nombre=datos["nombre"],
            descripcion=datos.get("descripcion", ""),
            direccion=datos.get("direccion", ""),
            telefono=datos.get("telefono", ""),
        ))
    elif tipo == "persona":
        if db.query(Persona).filter(Persona.email == datos["email"]).first():
            return "Ya existe una persona con ese correo."
        db.add(Persona(
            email=datos["email"],
            hashed_password=hashed,
            nombre=datos["nombre"],
            telefono=datos.get("telefono", ""),
        ))
    elif tipo == "transportista":
        if db.query(Transportista).filter(Transportista.email == datos["email"]).first():
            return "Ya existe un transportista con ese correo."
        db.add(Transportista(
            email=datos["email"],
            hashed_password=hashed,
            nombre=datos["nombre"],
            telefono=datos.get("telefono", ""),
            tipo_vehiculo=datos.get("tipo_vehiculo", "camioneta"),
            capacidad=datos.get("capacidad", "500 kg"),
            zona_cobertura=datos.get("zona_cobertura", "Local"),
            tarifa_base=datos.get("tarifa_base", 5000),
            costo_km=datos.get("costo_km", 1500),
        ))
    db.commit()
    return True

def cambiar_password(db: Session, email: str, password_actual: str, password_nueva: str):
    """Cambia la contraseña del usuario. Retorna mensaje de error o None."""
    usuario = db.query(Asociacion).filter(Asociacion.email == email).first()
    if not usuario:
        usuario = db.query(Persona).filter(Persona.email == email).first()
    if not usuario:
        usuario = db.query(Transportista).filter(Transportista.email == email).first()
    if not usuario:
        return "Usuario no encontrado."
    if not bcrypt.checkpw(password_actual.encode(), usuario.hashed_password.encode()):
        return "La contraseña actual es incorrecta."
    usuario.hashed_password = bcrypt.hashpw(password_nueva.encode(), bcrypt.gensalt()).decode()
    db.commit()
    return None