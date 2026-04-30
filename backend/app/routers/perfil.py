import logging
from fastapi import APIRouter, Request, Form, File, UploadFile, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Asociacion
import cloudinary.uploader

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger("perfil")

@router.get("/panel/editar-perfil", response_class=HTMLResponse)
def editar_perfil_form(request: Request, db: Session = Depends(get_db)):
    if "usuario" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    a = db.query(Asociacion).filter(Asociacion.email == email).first()
    if not a:
        return RedirectResponse(url="/panel", status_code=303)
    perfil = {
        "email": a.email,
        "nombre": a.nombre,
        "descripcion": a.descripcion,
        "direccion": a.direccion,
        "telefono": a.telefono,
        "logo_url": a.logo_url,
        "show_whatsapp": a.show_whatsapp,
        "camara_comercio_url": a.camara_url,
        "rut_url": a.rut_url
    }
    return templates.TemplateResponse("editar_perfil.html", {"request": request, "perfil": perfil})

@router.post("/panel/editar-perfil")
def actualizar_perfil(
    request: Request,
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
    if "usuario" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    a = db.query(Asociacion).filter(Asociacion.email == email).first()
    if not a:
        return RedirectResponse(url="/panel", status_code=303)

    from app.main import delete_cloudinary_asset

    if logo and logo.filename:
        if a.logo_url:
            delete_cloudinary_asset(a.logo_url, resource_type="image")
        try:
            result = cloudinary.uploader.upload(
                logo.file,
                folder="logos",
                filename=logo.filename,
                use_filename=True,
                unique_filename=True,
                access_mode="public"
            )
            a.logo_url = result.get("secure_url", "")
        except Exception:
            pass

    if camara_comercio and camara_comercio.filename:
        if a.camara_url:
            delete_cloudinary_asset(a.camara_url, resource_type="raw")
        try:
            result = cloudinary.uploader.upload(
                camara_comercio.file,
                folder="documentos",
                resource_type="raw",
                filename=camara_comercio.filename,
                use_filename=True,
                unique_filename=True,
                access_mode="public"
            )
            a.camara_url = result.get("secure_url", "")
        except Exception:
            pass

    if rut and rut.filename:
        if a.rut_url:
            delete_cloudinary_asset(a.rut_url, resource_type="raw")
        try:
            result = cloudinary.uploader.upload(
                rut.file,
                folder="documentos",
                resource_type="raw",
                filename=rut.filename,
                use_filename=True,
                unique_filename=True,
                access_mode="public"
            )
            a.rut_url = result.get("secure_url", "")
        except Exception:
            pass

    a.nombre = nombre_asociacion
    a.descripcion = descripcion or ""
    a.direccion = direccion or ""
    a.telefono = telefono or ""
    a.show_whatsapp = "1" if show_whatsapp == "1" else ""
    db.commit()

    request.session["nombre_asociacion"] = a.nombre
    request.session["logo_url"] = a.logo_url
    request.session["show_whatsapp"] = a.show_whatsapp
    request.session["telefono"] = a.telefono
    return RedirectResponse(url="/panel", status_code=303)