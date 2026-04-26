import os
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path
from .database import engine
from . import models
from .dependencies import templates
from .routers import auth, publico, asociaciones, productos

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear tablas en la base de datos
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

SECRET_KEY = os.getenv("SECRET_KEY", "clave-secreta-cambiar-urgente")
IS_PRODUCTION = os.getenv("RENDER", "false").lower() == "true"

logger.info(f"IS_PRODUCTION = {IS_PRODUCTION}")

# Configuración de la cookie de sesión para Render (HTTPS)
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    max_age=604800,          # 7 días
    https_only=IS_PRODUCTION,   # Enviar solo en HTTPS en producción
    same_site="lax"              # Funciona bien con subdominios de Render
)

# Archivos estáticos (CSS, JS, imágenes)
static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Incluir los routers
app.include_router(auth.router)
app.include_router(publico.router)
app.include_router(asociaciones.router)
app.include_router(productos.router)

logger.info("Aplicación iniciada correctamente")