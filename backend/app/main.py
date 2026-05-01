import logging
import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.auth import router as auth_router
from app.database import engine, Base, SessionLocal
from app.models import Configuracion
import cloudinary
import time

# Routers existentes
from app.routers import home, catalogo, dashboard, panel, perfil, asociacion, valoraciones, admin, calculadora
# NUEVOS routers
from app.routers import personas, empleos

logging.basicConfig(level=logging.INFO)

app = FastAPI()

cloudinary.config(cloudinary_url=os.getenv("CLOUDINARY_URL"))

SECRET_KEY = os.getenv("SECRET_KEY", "dev_key")

# ─── Middleware de sesión y timeout ──────
class SessionTimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.session.get("usuario"):
            last_activity = request.session.get("last_activity", 0)
            now = time.time()
            if now - last_activity > 120:
                request.session.clear()
                from fastapi.responses import RedirectResponse
                return RedirectResponse(url="/auth/login", status_code=303)
            request.session["last_activity"] = now
        response = await call_next(request)
        return response

app.add_middleware(SessionTimeoutMiddleware)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, same_site="lax", https_only=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Middleware de configuración SEO / Diseño ──────
@app.middleware("http")
async def cargar_configuracion(request: Request, call_next):
    db = SessionLocal()
    try:
        config = db.query(Configuracion).first()
        if not config:
            config = Configuracion()
            db.add(config)
            db.commit()
            db.refresh(config)
        request.state.config = config
    finally:
        db.close()
    response = await call_next(request)
    return response

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Incluir routers
app.include_router(auth_router, prefix="/auth")
app.include_router(home.router)
app.include_router(catalogo.router)
app.include_router(dashboard.router)
app.include_router(panel.router)
app.include_router(perfil.router)
app.include_router(asociacion.router)
app.include_router(valoraciones.router)
app.include_router(admin.router)
app.include_router(calculadora.router)
# NUEVOS
app.include_router(personas.router)
app.include_router(empleos.router)

# Utilidad para eliminar assets de Cloudinary
def delete_cloudinary_asset(url: str, resource_type: str = "image"):
    if not url or "cloudinary.com" not in url:
        return
    try:
        parts = url.split("/")
        upload_idx = -1
        for i, part in enumerate(parts):
            if part == "upload":
                upload_idx = i
                break
        if upload_idx == -1 or upload_idx + 2 >= len(parts):
            return
        public_id_with_ext = "/".join(parts[upload_idx + 2:])
        if resource_type in ("image", "video"):
            public_id = public_id_with_ext.rsplit(".", 1)[0]
        else:
            public_id = public_id_with_ext
        cloudinary.uploader.destroy(public_id, resource_type=resource_type)
    except Exception:
        pass

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)