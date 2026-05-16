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
    """Inicia sesión y devuelve JSON con los datos del usuario."""
    usuario_dict = autenticar_usuario(db, email, password)
    if not usuario_dict:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    # Obtener el objeto real para acceder a region y otros campos
    tipo = usuario_dict["tipo"]
    if tipo == "asociacion":
        usuario = db.query(Asociacion).filter(Asociacion.email == email).first()
    elif tipo == "persona":
        usuario = db.query(Persona).filter(Persona.email == email).first()
    elif tipo == "transportista":
        usuario = db.query(Transportista).filter(Transportista.email == email).first()
    else:
        usuario = None

    # Guardar datos en sesión
    request.session["usuario"] = email
    request.session["tipo_usuario"] = tipo
    region = getattr(usuario, "region", None) if usuario else None
    request.session["region"] = region

    return JSONResponse({
        "email": email,
        "nombre": usuario_dict["nombre"],
        "tipo": tipo,
        "region": region,
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
    """Registra un nuevo usuario y devuelve sus datos."""
    # Verificar si el email ya existe en alguna tabla
    for model in [Asociacion, Persona, Transportista]:
        if db.query(model).filter(model.email == email).first():
            raise HTTPException(status_code=400, detail="El email ya está registrado")

    hashed = hash_password(password)
    if tipo == "asociacion":
        nuevo = Asociacion(
            email=email,
            hashed_password=hashed,
            nombre=nombre,
            telefono=telefono,
            region=region,
        )
    elif tipo == "persona":
        nuevo = Persona(
            email=email,
            hashed_password=hashed,
            nombre=nombre,
            telefono=telefono,
            region=region,
        )
    elif tipo == "transportista":
        nuevo = Transportista(
            email=email,
            hashed_password=hashed,
            nombre=nombre,
            telefono=telefono,
            region=region,
        )
    else:
        raise HTTPException(status_code=400, detail="Tipo de usuario no válido")

    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    # Iniciar sesión automáticamente
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