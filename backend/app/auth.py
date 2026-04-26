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
        sheet = get_sheet()
        registros = sheet.get_all_values()[1:]  # Saltar encabezados

        for fila in registros:
            # Columna 0 = email, columna 1 = hash
            if fila[0] == email:
                hashed = fila[1].encode("utf-8")
                password_bytes = password.encode("utf-8")[:72]
                if bcrypt.checkpw(password_bytes, hashed):
                    request.session["usuario"] = email
                    # Guardar también el nombre de la asociación en sesión (columna 3)
                    if len(fila) > 3:
                        request.session["nombre_asociacion"] = fila[3]
                    return RedirectResponse(url="/panel", status_code=303)
                else:
                    return templates.TemplateResponse(
                        "login.html",
                        {"request": request, "error": "Credenciales incorrectas"}
                    )

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
    password: str = Form(...),
    nombre_asociacion: str = Form(...),
    descripcion: str = Form(None),
    direccion: str = Form(None),
    telefono: str = Form(None),
):
    try:
        sheet = get_sheet()
        registros = sheet.get_all_values()[1:]

        # Verificar si el email ya existe (columna 0)
        for fila in registros:
            if fila[0] == email:
                return templates.TemplateResponse(
                    "registro.html",
                    {"request": request, "error": "Este email ya está registrado."}
                )

        # Hashear contraseña
        password_bytes = password.encode("utf-8")[:72]
        hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")

        # Guardar nueva fila (8 columnas)
        sheet.append_row([
            email,                         # A
            hashed,                        # B
            str(datetime.datetime.now()),  # C
            nombre_asociacion,             # D
            descripcion or "",             # E
            direccion or "",               # F
            telefono or "",                # G
            ""                             # H (Logo URL, vacío por ahora)
        ])

        logger.info("Asociación registrada: %s (%s)", nombre_asociacion, email)
        return RedirectResponse(url="/auth/login", status_code=303)

    except Exception as e:
        logger.exception("Error al guardar en Google Sheets")
        return templates.TemplateResponse(
            "registro.html",
            {"request": request, "error": "No se pudo completar el registro. Intenta más tarde."}
        )