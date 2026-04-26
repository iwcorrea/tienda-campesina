import logging
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
import os
from app.auth import router as auth_router
from app.database import engine, Base, SessionLocal
from app.models import Producto
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Crear las tablas al arrancar si no existen
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

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

# Dependencia para obtener la sesión de BD
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# HOME
@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
def inicio(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# MENÚ
@app.get("/menu", response_class=HTMLResponse)
def menu(request: Request):
    return templates.TemplateResponse("menu.html", {"request": request})

# CATÁLOGO (datos reales desde SQLite)
@app.get("/catalogo", response_class=HTMLResponse)
def catalogo(request: Request, db: Session = Depends(get_db)):
    productos_db = db.query(Producto).filter(Producto.disponible == 1).order_by(Producto.fecha_creacion.desc()).all()
    productos = []
    for p in productos_db:
        productos.append({
            "nombre": p.nombre,
            "descripcion": p.descripcion or "",
            "precio": p.precio,
            "imagen": p.imagen_url or "https://placehold.co/300x200/5B8C51/white?text=Producto",
            "asociacion": p.asociacion_email
        })
    return templates.TemplateResponse("catalogo.html", {"request": request, "productos": productos})

# PANEL (protegido)
@app.get("/panel", response_class=HTMLResponse)
def panel(request: Request, db: Session = Depends(get_db)):
    if "usuario" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    productos_db = db.query(Producto).filter(Producto.asociacion_email == email).order_by(Producto.fecha_creacion.desc()).all()
    return templates.TemplateResponse("panel.html", {
        "request": request,
        "usuario": request.session.get("nombre_asociacion", email),
        "productos": productos_db
    })

# CREAR PRODUCTO (POST desde el panel)
@app.post("/panel/producto")
def crear_producto(
    request: Request,
    nombre: str = Form(...),
    descripcion: str = Form(None),
    precio: int = Form(...),
    imagen_url: str = Form(None),
    db: Session = Depends(get_db)
):
    if "usuario" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=303)

    email = request.session["usuario"]
    nuevo = Producto(
        asociacion_email=email,
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        imagen_url=imagen_url or ""
    )
    db.add(nuevo)
    db.commit()
    return RedirectResponse(url="/panel", status_code=303)