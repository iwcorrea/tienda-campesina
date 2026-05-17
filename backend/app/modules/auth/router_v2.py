from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import bcrypt
from app.dependencies import get_db
from app.modules.auth.service import autenticar_usuario
from app.models import Asociacion, Persona, Transportista

router = APIRouter(prefix="/auth", tags=["auth_v2"])

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

@router.post("/login")
def login_v2(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    resultado = autenticar_usuario(db, email, password)
    if not resultado:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    tipo, nombre, es_admin = resultado

    request.session["usuario"] = email
    request.session["tipo_usuario"] = tipo
    if es_admin:
        request.session["es_admin"] = True

    region = None
    if tipo == "asociacion":
        usuario = db.query(Asociacion).filter(Asociacion.email == email).first()
    elif tipo == "persona":
        usuario = db.query(Persona).filter(Persona.email == email).first()
    elif tipo == "transportista":
        usuario = db.query(Transportista).filter(Transportista.email == email).first()
    else:
        usuario = None

    if usuario and hasattr(usuario, "region"):
        region = usuario.region
        request.session["region"] = region

    return JSONResponse({
        "email": email,
        "nombre": nombre,
        "tipo": tipo,
        "region": region,
        "es_admin": es_admin,
    })

@router.post("/register", status_code=201)
def register_v2(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    tipo: str = Form(...),
    nombre: str = Form(...),
    telefono: str = Form(""),
    region: str = Form(None),
    db: Session = Depends(get_db),
):
    for model in [Asociacion, Persona, Transportista]:
        if db.query(model).filter(model.email == email).first():
            raise HTTPException(status_code=400, detail="El email ya está registrado")

    hashed = hash_password(password)
    if tipo == "asociacion":
        nuevo = Asociacion(email=email, hashed_password=hashed, nombre=nombre,
                           telefono=telefono, region=region)
    elif tipo == "persona":
        nuevo = Persona(email=email, hashed_password=hashed, nombre=nombre,
                        telefono=telefono, region=region)
    elif tipo == "transportista":
        nuevo = Transportista(email=email, hashed_password=hashed, nombre=nombre,
                              telefono=telefono, region=region)
    else:
        raise HTTPException(status_code=400, detail="Tipo de usuario no válido")

    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    request.session["usuario"] = email
    request.session["tipo_usuario"] = tipo
    request.session["region"] = region

    return JSONResponse({
        "email": email,
        "nombre": nombre,
        "tipo": tipo,
        "region": region,
    })

@router.post("/logout")
def logout_v2(request: Request):
    request.session.clear()
    return JSONResponse({"mensaje": "Sesión cerrada"})