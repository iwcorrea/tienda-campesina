from fastapi import APIRouter, Request, Form, File, UploadFile, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import bcrypt
from app.database import get_db
from app.models import Asociacion
import cloudinary.uploader
import logging
import datetime
import os

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger("auth")

ADMIN_EMAILS = [e.strip().lower() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()]

@router.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login_post(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    try:
        user = db.query(Asociacion).filter(Asociacion.email == email).first()
        if user:
            password_bytes = password.encode("utf-8")[:72]
            if bcrypt.checkpw(password_bytes, user.hashed_password.encode("utf-8")):
                request.session["usuario"] = user.email
                request.session["nombre_asociacion"] = user.nombre
                request.session["logo_url"] = user.logo_url
                request.session["show_whatsapp"] = user.show_whatsapp
                request.session["telefono"] = user.telefono
                request.session["verificado"] = user.verificado

                if email.lower() in ADMIN_EMAILS:
                    request.session["es_admin"] = True
                    return RedirectResponse(url="/admin", status_code=303)

                return RedirectResponse(url="/panel", status_code=303)
            else:
                return templates.TemplateResponse("login.html", {"request": request, "error": "Credenciales incorrectas"})
        return templates.TemplateResponse("login.html", {"request": request, "error": "Credenciales incorrectas"})
    except Exception as e:
        logger.exception("Error en login_post")
        return templates.TemplateResponse("login.html", {"request": request, "error": "Ocurrió un error inesperado."})

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

@router.get("/registro", response_class=HTMLResponse)
def registro_get(request: Request):
    return templates.TemplateResponse("registro.html", {"request": request})

@router.post("/registro")
def registro_post(
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
    try:
        if db.query(Asociacion).filter(Asociacion.email == email).first():
            return templates.TemplateResponse("registro.html", {"request": request, "error": "Este email ya está registrado."})

        logo_url = upload_file_cloudinary(logo, "logos")
        camara_url = upload_file_cloudinary(camara_comercio, "documentos", raw=True)
        rut_url = upload_file_cloudinary(rut, "documentos", raw=True)

        hashed = bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")

        nueva = Asociacion(
            email=email,
            hashed_password=hashed,
            nombre=nombre_asociacion,
            descripcion=descripcion or "",
            direccion=direccion or "",
            telefono=telefono or "",
            logo_url=logo_url,
            show_whatsapp="1" if show_whatsapp == "1" else "",
            camara_url=camara_url,
            rut_url=rut_url,
            verificado=""
        )
        db.add(nueva)
        db.commit()

        logger.info("Asociación registrada: %s (%s)", nombre_asociacion, email)
        return RedirectResponse(url="/auth/login", status_code=303)

    except Exception as e:
        logger.exception("Error al guardar en base de datos")
        return templates.TemplateResponse("registro.html", {"request": request, "error": "No se pudo completar el registro. Intenta más tarde."})

def upload_file_cloudinary(file: UploadFile, folder: str, raw: bool = False):
    if not file or not file.filename:
        return ""
    try:
        kwargs = dict(
            folder=folder,
            filename=file.filename,
            use_filename=True,
            unique_filename=True,
            access_mode="public"
        )
        if raw:
            kwargs["resource_type"] = "raw"
        result = cloudinary.uploader.upload(file.file, **kwargs)
        return result.get("secure_url", "")
    except Exception:
        return ""