from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="backend/app/templates")


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
    # ⚠️ Aquí luego validamos con DB o Google Sheets
    if email == "admin@test.com" and password == "1234":
        return RedirectResponse(url="/inicio", status_code=303)

    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": "Credenciales incorrectas"}
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
    # ⚠️ Aquí luego guardamos en Google Sheets
    print("Nuevo usuario:", email)

    return RedirectResponse(url="/auth/login", status_code=303)