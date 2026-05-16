from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.modules.auth.service import (
    autenticar_usuario,
    registrar_asociacion,
    registrar_persona,
    registrar_transportista,
)
from app.models import Asociacion, Persona, Transportista

router = APIRouter(prefix="/auth", tags=["auth_v2"])

@router.post("/login")
def login_v2(request: Request, email: str, password: str, db: Session = Depends(get_db)):
    """
    Inicia sesión y devuelve JSON con los datos del usuario.
    Guarda la sesión en el servidor (cookie).
    """
    usuario = autenticar_usuario(db, email, password)
    if not usuario:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    # Guardar datos en sesión
    request.session["usuario"] = email
    request.session["tipo_usuario"] = usuario.tipo
    request.session["region"] = usuario.region if hasattr(usuario, "region") else None

    return JSONResponse({
        "email": usuario.email,
        "nombre": usuario.nombre,
        "tipo": usuario.tipo,
        "region": usuario.region if hasattr(usuario, "region") else None,
    })

@router.post("/register", status_code=201)
def register_v2(
    request: Request,
    email: str,
    password: str,
    tipo: str,  # "asociacion", "persona", "transportista"
    nombre: str,
    telefono: str = "",
    region: str = None,
    db: Session = Depends(get_db),
):
    """
    Registra un nuevo usuario y devuelve sus datos.
    """
    if tipo == "asociacion":
        usuario = registrar_asociacion(db, email, password, nombre, telefono, region)
    elif tipo == "persona":
        usuario = registrar_persona(db, email, password, nombre, telefono, region)
    elif tipo == "transportista":
        usuario = registrar_transportista(db, email, password, nombre, telefono, region)
    else:
        raise HTTPException(status_code=400, detail="Tipo de usuario no válido")

    # Iniciar sesión automáticamente
    request.session["usuario"] = email
    request.session["tipo_usuario"] = tipo
    request.session["region"] = region

    return JSONResponse({
        "email": usuario.email,
        "nombre": usuario.nombre,
        "tipo": tipo,
        "region": region,
    })

@router.post("/logout")
def logout_v2(request: Request):
    request.session.clear()
    return JSONResponse({"mensaje": "Sesión cerrada"})