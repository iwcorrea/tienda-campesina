from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import bcrypt
from app.google_sheets import get_sheet
import logging
import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger("auth")

# ------------------- LOGIN -------------------
@router.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    try:
        # Login temporal (luego leeremos de Google Sheets)
        if email == "admin@test.com" and password == "1234":
            request.session["usuario"] = email
            return RedirectResponse(url="/catalogo", status_code=303)

        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Credenciales incorrectas"}
        )
    except Exception as e:
        logger.exception("Error en login_post")
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Ocurrió un error inesperado."}
        )


# ------------------- REGISTRO -------------------
@router.get("/registro", response_class=HTMLResponse)
def registro_get(request: Request):
    return templates.TemplateResponse("registro.html", {"request": request})


@router.post("/registro")
def registro_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    try:
        # Truncar contraseña a 72 bytes (límite de bcrypt) por seguridad
        password_bytes = password.encode("utf-8")[:72]
        # Hashear con bcrypt
        hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")

        # Guardar en Google Sheets
        sheet = get_sheet()
        sheet.append_row([
            email,
            hashed,
            str(datetime.datetime.now())
        ])

        logger.info("Usuario registrado en Google Sheets: %s", email)
        return RedirectResponse(url="/auth/login", status_code=303)

    except Exception as e:
        logger.exception("Error al guardar en Google Sheets")
        return templates.TemplateResponse(
            "registro.html",
            {"request": request, "error": "No se pudo completar el registro. Intenta más tarde."}
        )