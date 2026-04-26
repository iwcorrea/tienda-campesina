from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import logging

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger("auth")  # opcional, para logs

# 🔐 LOGIN
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
        # ⚠️ Aquí luego validamos con DB o Google Sheets
        if email == "admin@test.com" and password == "1234":
            # ✅ Guardamos el email en la sesión
            request.session["usuario"] = email
            # 🔁 Redirigimos a una ruta que sí existe
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


# 📝 REGISTRO
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
        # ⚠️ Aquí luego guardamos en Google Sheets
        logger.info("Nuevo usuario registrado: %s", email)
        return RedirectResponse(url="/auth/login", status_code=303)
    except Exception as e:
        logger.exception("Error en registro_post")
        return templates.TemplateResponse(
            "registro.html",
            {"request": request, "error": "Ocurrió un error inesperado."}
        )