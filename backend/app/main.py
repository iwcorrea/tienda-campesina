import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
import os
from app.auth import router as auth_router

# Configurar logging para ver errores en los logs de Render
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Seguridad
SECRET_KEY = os.getenv("SECRET_KEY", "dev_key")
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="lax",
    https_only=True,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates
templates = Jinja2Templates(directory="app/templates")

# Static (CSS, imágenes)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Rutas de auth
app.include_router(auth_router, prefix="/auth")

# HOME (acepta GET y HEAD)
@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
def inicio(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# MENÚ
@app.get("/menu", response_class=HTMLResponse)
def menu(request: Request):
    return templates.TemplateResponse("menu.html", {"request": request})

# CATÁLOGO
@app.get("/catalogo", response_class=HTMLResponse)
def catalogo(request: Request):
    return templates.TemplateResponse("catalogo.html", {"request": request})