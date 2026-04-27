from fastapi import APIRouter, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import bcrypt
from app.google_sheets import get_sheet
import cloudinary.uploader
import logging
import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger("auth")

@router.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login_post(request: Request, email: str = Form(...), password: str = Form(...)):
    try:
        sheet = get_sheet()
        registros = sheet.get_all_values()[1:]
        for fila in registros:
            if fila[0] == email:
                hashed = fila[1].encode("utf-8")
                password_bytes = password.encode("utf-8")[:72]
                if bcrypt.checkpw(password_bytes, hashed):
                    request.session["usuario"] = email
                    if len(fila) > 3:
                        request.session["nombre_asociacion"] = fila[3]
                    if len(fila) > 7 and fila[7].strip():
                        request.session["logo_url"] = fila[7].strip()
                    if len(fila) > 8:
                        request.session["show_whatsapp"] = fila[8].strip()
                    if len(fila) > 6:
                        request.session["telefono"] = fila[6].strip()
                    if len(fila) > 11:
                        request.session["verificado"] = fila[11].strip()
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
    rut: UploadFile = File(None)
):
    try:
        sheet = get_sheet()
        registros = sheet.get_all_values()[1:]
        for fila in registros:
            if fila[0] == email:
                return templates.TemplateResponse("registro.html", {"request": request, "error": "Este email ya está registrado."})

        logo_url = ""
        if logo and logo.filename:
            try:
                result = cloudinary.uploader.upload(logo.file, folder="logos")
                logo_url = result.get("secure_url", "")
            except Exception:
                pass

        camara_url = ""
        if camara_comercio and camara_comercio.filename:
            try:
                result = cloudinary.uploader.upload(camara_comercio.file, folder="documentos", resource_type="raw")
                camara_url = result.get("secure_url", "")
            except Exception:
                pass

        rut_url = ""
        if rut and rut.filename:
            try:
                result = cloudinary.uploader.upload(rut.file, folder="documentos", resource_type="raw")
                rut_url = result.get("secure_url", "")
            except Exception:
                pass

        password_bytes = password.encode("utf-8")[:72]
        hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")

        sheet.append_row([
            email,
            hashed,
            str(datetime.datetime.now()),
            nombre_asociacion,
            descripcion or "",
            direccion or "",
            telefono or "",
            logo_url,
            "1" if show_whatsapp == "1" else "",
            camara_url,
            rut_url,
            ""   # verificado vacío
        ])

        logger.info("Asociación registrada: %s (%s)", nombre_asociacion, email)
        return RedirectResponse(url="/auth/login", status_code=303)

    except Exception as e:
        logger.exception("Error al guardar en Google Sheets")
        return templates.TemplateResponse("registro.html", {"request": request, "error": "No se pudo completar el registro. Intenta más tarde."})