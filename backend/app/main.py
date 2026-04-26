from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import os

from app.auth import router as auth_router

app = FastAPI()

# 🔐 Configuración de sesiones
SECRET_KEY = os.getenv("SECRET_KEY", "dev_key")

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="lax",
    https_only=True,
)

# 📁 Templates
templates = Jinja2Templates(directory="app/templates")

# 🔗 Rutas auth
app.include_router(auth_router, prefix="/auth")


# 🔥 HOME → usa tu index.html bonito
@app.get("/")
def home():
    return RedirectResponse(url="/inicio")


@app.get("/inicio")
def inicio(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# 🔥 MENÚ
@app.get("/menu")
def menu(request: Request):
    return templates.TemplateResponse("menu.html", {"request": request})


# 🔥 CATÁLOGO
@app.get("/catalogo")
def catalogo(request: Request):
    return templates.TemplateResponse("catalogo.html", {"request": request})