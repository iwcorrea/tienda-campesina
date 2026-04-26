import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
import os
from app.auth import router as auth_router

logging.basicConfig(level=logging.INFO)

app = FastAPI()

SECRET_KEY = os.getenv("SECRET_KEY", "dev_key")
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="lax",
    https_only=True,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(auth_router, prefix="/auth")

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
def inicio(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/menu", response_class=HTMLResponse)
def menu(request: Request):
    return templates.TemplateResponse("menu.html", {"request": request})

@app.get("/catalogo", response_class=HTMLResponse)
def catalogo(request: Request):
    # Datos de ejemplo (luego vendrán de base de datos)
    productos_ejemplo = [
        {
            "nombre": "Café orgánico",
            "descripcion": "Café arábigo cultivado en sombra, 500g.",
            "precio": 18000,
            "imagen": "https://placehold.co/300x200/5B8C51/white?text=Café",
            "asociacion": "Asociación El Café del Valle"
        },
        {
            "nombre": "Miel de abejas nativas",
            "descripcion": "Miel pura de melipona, 250ml.",
            "precio": 15000,
            "imagen": "https://placehold.co/300x200/E8B042/white?text=Miel",
            "asociacion": "Mieles del Cauca"
        },
        {
            "nombre": "Canasto artesanal",
            "descripcion": "Tejido en fibra de plátano, 30cm.",
            "precio": 25000,
            "imagen": "https://placehold.co/300x200/8B5A2B/white?text=Artesanía",
            "asociacion": "Artesanos de la Montaña"
        }
    ]
    return templates.TemplateResponse("catalogo.html", {"request": request, "productos": productos_ejemplo})

@app.get("/panel", response_class=HTMLResponse)
def panel(request: Request):
    if "usuario" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=303)
    return templates.TemplateResponse("panel.html", {
        "request": request,
        "usuario": request.session.get("nombre_asociacion", request.session["usuario"])
    })