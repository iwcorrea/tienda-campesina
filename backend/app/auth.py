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
        # Buscar al usuario en Google Sheets
        sheet = get_sheet()
        registros = sheet.get_all_values()

        for fila in registros:
            # Suponemos columnas: 0=Email, 1=Contraseña (hash), 2=Fecha
            if fila[0] == email:
                hashed = fila[1].encode("utf-8")
                password_bytes = password.encode("utf-8")[:72]
                if bcrypt.checkpw(password_bytes, hashed):
                    # Éxito: guardar sesión
                    request.session["usuario"] = email
                    return RedirectResponse(url="/catalogo", status_code=303)
                else:
                    # Contraseña incorrecta
                    return templates.TemplateResponse(
                        "login.html",
                        {"request": request, "error": "Credenciales incorrectas"}
                    )

        # Si no se encontró el email
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
        # Validación simple: evitar duplicados
        sheet = get_sheet()
        registros = sheet.get_all_values()
        for fila in registros:
            if fila[0] == email:
                return templates.TemplateResponse(
                    "registro.html",
                    {"request": request, "error": "Este email ya está registrado."}
                )

        # Hashear contraseña
        password_bytes = password.encode("utf-8")[:72]
        hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")

        # Guardar en Google Sheets
        sheet.append_row([email, hashed, str(datetime.datetime.now())])

        logger.info("Usuario registrado en Google Sheets: %s", email)
        return RedirectResponse(url="/auth/login", status_code=303)

    except Exception as e:
        logger.exception("Error al guardar en Google Sheets")
        return templates.TemplateResponse(
            "registro.html",
            {"request": request, "error": "No se pudo completar el registro. Intenta más tarde."}
        )