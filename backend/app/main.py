from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path
from .database import engine
from . import models
from .dependencies import templates
from .routers import auth, publico, asociaciones, productos
import os

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

SECRET_KEY = os.getenv("SECRET_KEY", "clave-secreta-cambiar")
IS_PRODUCTION = os.getenv("RENDER", "false").lower() == "true"

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    https_only=IS_PRODUCTION,
    same_site="lax",
    domain=".onrender.com" if IS_PRODUCTION else None,
)

static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.include_router(auth.router)
app.include_router(publico.router)
app.include_router(asociaciones.router)
app.include_router(productos.router)