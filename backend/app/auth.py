from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


# 🔐 LOGIN (GET)
@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# 🔐 LOGIN (POST)
@router.post("/login")
def login_user(email: str = Form(...), password: str = Form(...)):
    # 🔴 lógica falsa por ahora
    if email == "admin@test.com" and password == "1234":
        return RedirectResponse(url="/menu", status_code=302)
    
    return templates.TemplateResponse("login.html", {
        "request": {},
        "error": "Credenciales incorrectas"
    })


# 📝 REGISTRO (GET)
@router.get("/registro", response_class=HTMLResponse)
def registro_form(request: Request):
    return templates.TemplateResponse("registro.html", {"request": request})


# 📝 REGISTRO (POST)
@router.post("/registro")
def registrar_usuario(nombre: str = Form(...), email: str = Form(...)):
    # 🔴 aquí luego conectamos Google Sheets
    return RedirectResponse(url="/menu", status_code=302)