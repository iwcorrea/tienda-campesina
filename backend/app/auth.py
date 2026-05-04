from fastapi import APIRouter, Request, Form, File, UploadFile, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import bcrypt
from app.database import get_db
from app.models import Asociacion, Persona
import cloudinary.uploader
import logging
import datetime
import os
import time

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger("auth")

ADMIN_EMAILS = [e.strip().lower() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()]

def upload_file_cloudinary(file: UploadFile, folder: str, raw: bool = False):
    if not file or not file.filename:
        return ""
    try:
        kwargs = dict(folder=folder, filename=file.filename, use_filename=True, unique_filename=True, access_mode="public")
        if raw:
            kwargs["resource_type"] = "raw"
        result = cloudinary.uploader.upload(file.file, **kwargs)
        return result.get("secure_url", "")
    except Exception:
        return ""

# ─── LOGIN UNIFICADO ──────────────────────────────────
@router.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login_post(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    try:
        asoc = db.query(Asociacion).filter(Asociacion.email == email).first()
        if asoc:
            if bcrypt.checkpw(password.encode("utf-8")[:72], asoc.hashed_password.encode("utf-8")):
                request.session["usuario"] = asoc.email
                request.session["tipo_usuario"] = "asociacion"
                request.session["nombre_usuario"] = asoc.nombre
                request.session["logo_url"] = asoc.logo_url or ""
                request.session["show_whatsapp"] = asoc.show_whatsapp
                request.session["telefono"] = asoc.telefono
                request.session["verificado"] = asoc.verificado
                request.session["last_activity"] = time.time()
                if email.lower() in ADMIN_EMAILS:
                    request.session["es_admin"] = True
                    return RedirectResponse(url="/admin", status_code=303)
                return RedirectResponse(url="/panel", status_code=303)
        persona = db.query(Persona).filter(Persona.email == email).first()
        if persona:
            if bcrypt.checkpw(password.encode("utf-8")[:72], persona.hashed_password.encode("utf-8")):
                request.session["usuario"] = persona.email
                request.session["tipo_usuario"] = "persona"
                request.session["nombre_usuario"] = persona.nombre
                request.session["last_activity"] = time.time()
                return RedirectResponse(url="/perfil", status_code=303)
        return templates.TemplateResponse("login.html", {"request": request, "error": "Credenciales incorrectas"})
    except Exception as e:
        logger.exception("Error en login_post")
        return templates.TemplateResponse("login.html", {"request": request, "error": "Ocurrió un error inesperado."})

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

# ─── REGISTRO DE ASOCIACIÓN (sin cambios) ──────────
@router.get("/registro", response_class=HTMLResponse)
def registro_asociacion_get(request: Request):
    if request.session.get("usuario"):
        return RedirectResponse(url="/panel" if request.session.get("tipo_usuario")=="asociacion" else "/perfil", status_code=303)
    return templates.TemplateResponse("registro.html", {"request": request})

@router.post("/registro")
def registro_asociacion_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    nombre_asociacion: str = Form(...),
    descripcion: str = Form(None),
    direccion: str = Form(None),
    telefono: str = Form(None),
    show_whatsapp: str = Form(None),
    logo: UploadFile = File(None),
    camara_comercio: UploadFile = File(None),
    rut: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    if db.query(Asociacion).filter(Asociacion.email == email).first() or db.query(Persona).filter(Persona.email == email).first():
        return templates.TemplateResponse("registro.html", {"request": request, "error": "Este email ya está registrado."})
    logo_url = upload_file_cloudinary(logo, "logos")
    camara_url = upload_file_cloudinary(camara_comercio, "documentos", raw=True)
    rut_url = upload_file_cloudinary(rut, "documentos", raw=True)
    hashed = bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")
    nueva = Asociacion(
        email=email, hashed_password=hashed, nombre=nombre_asociacion,
        descripcion=descripcion or "", direccion=direccion or "", telefono=telefono or "",
        logo_url=logo_url, show_whatsapp="1" if show_whatsapp=="1" else "",
        camara_url=camara_url, rut_url=rut_url, verificado=""
    )
    db.add(nueva)
    db.commit()
    logger.info("Asociación registrada: %s (%s)", nombre_asociacion, email)
    return RedirectResponse(url="/auth/login", status_code=303)

# ─── REGISTRO DE PERSONA (sin cambios) ──────────────
@router.get("/registro-persona", response_class=HTMLResponse)
def registro_persona_get(request: Request):
    if request.session.get("usuario"):
        return RedirectResponse(url="/perfil" if request.session.get("tipo_usuario")=="persona" else "/panel", status_code=303)
    return templates.TemplateResponse("registro_persona.html", {"request": request})

@router.post("/registro-persona")
def registro_persona_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    nombre: str = Form(...),
    telefono: str = Form(None),
    hoja_vida: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    if db.query(Asociacion).filter(Asociacion.email == email).first() or db.query(Persona).filter(Persona.email == email).first():
        return templates.TemplateResponse("registro_persona.html", {"request": request, "error": "Este email ya está registrado."})
    hoja_url = upload_file_cloudinary(hoja_vida, "hojas_vida", raw=True)
    hashed = bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")
    nueva = Persona(email=email, hashed_password=hashed, nombre=nombre, telefono=telefono or "", hoja_vida_url=hoja_url)
    db.add(nueva)
    db.commit()
    logger.info("Persona registrada: %s (%s)", nombre, email)
    return RedirectResponse(url="/auth/login", status_code=303)

# ─── CAMBIO DE CONTRASEÑA (UNIFICADO) ─────────────────
@router.get("/cambiar-password", response_class=HTMLResponse)
def cambiar_password_get(request: Request):
    if not request.session.get("usuario"):
        return RedirectResponse(url="/auth/login", status_code=303)
    return templates.TemplateResponse("cambiar_password.html", {"request": request})

@router.post("/cambiar-password")
def cambiar_password_post(
    request: Request,
    password_actual: str = Form(...),
    password_nueva: str = Form(...),
    password_repite: str = Form(...),
    db: Session = Depends(get_db)
):
    if not request.session.get("usuario"):
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    tipo = request.session.get("tipo_usuario")
    error = None

    if password_nueva != password_repite:
        error = "Las contraseñas nuevas no coinciden."
    elif len(password_nueva) < 6:
        error = "La nueva contraseña debe tener al menos 6 caracteres."
    else:
        if tipo == "asociacion":
            user = db.query(Asociacion).filter(Asociacion.email == email).first()
        elif tipo == "persona":
            user = db.query(Persona).filter(Persona.email == email).first()
        else:
            return RedirectResponse(url="/auth/login", status_code=303)

        if user and bcrypt.checkpw(password_actual.encode("utf-8")[:72], user.hashed_password.encode("utf-8")):
            nuevo_hash = bcrypt.hashpw(password_nueva.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")
            user.hashed_password = nuevo_hash
            db.commit()
            return RedirectResponse(url="/perfil" if tipo=="persona" else "/panel", status_code=303)
        else:
            error = "La contraseña actual es incorrecta."

    return templates.TemplateResponse("cambiar_password.html", {"request": request, "error": error})