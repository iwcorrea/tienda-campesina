from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.models import Asociacion, Persona, Transportista

router = APIRouter(tags=["users_v2"])

@router.get("/me")
def get_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="No autenticado")

    email = current_user["email"]
    tipo = current_user["tipo"]
    if tipo == "asociacion":
        usuario = db.query(Asociacion).filter(Asociacion.email == email).first()
    elif tipo == "persona":
        usuario = db.query(Persona).filter(Persona.email == email).first()
    elif tipo == "transportista":
        usuario = db.query(Transportista).filter(Transportista.email == email).first()
    else:
        raise HTTPException(status_code=400, detail="Tipo de usuario desconocido")

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return {
        "email": usuario.email,
        "nombre": usuario.nombre,
        "tipo": tipo,
        "region": getattr(usuario, "region", None),
        "telefono": getattr(usuario, "telefono", ""),
    }

@router.patch("/me")
def update_profile(
    nombre: str = None,
    telefono: str = None,
    region: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="No autenticado")

    email = current_user["email"]
    tipo = current_user["tipo"]
    usuario = None
    if tipo == "asociacion":
        usuario = db.query(Asociacion).filter(Asociacion.email == email).first()
    elif tipo == "persona":
        usuario = db.query(Persona).filter(Persona.email == email).first()
    elif tipo == "transportista":
        usuario = db.query(Transportista).filter(Transportista.email == email).first()
    else:
        raise HTTPException(status_code=400)

    if not usuario:
        raise HTTPException(status_code=404)

    if nombre is not None:
        usuario.nombre = nombre
    if telefono is not None:
        usuario.telefono = telefono
    if region is not None:
        usuario.region = region

    db.commit()
    return {"mensaje": "Perfil actualizado"}