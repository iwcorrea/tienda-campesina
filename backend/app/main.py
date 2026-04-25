from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from .routers import auth, publico, asociaciones, productos
from .database import engine
from . import models

# Crear tablas
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Configuración de templates y estáticos
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Incluir routers
app.include_router(auth.router)
app.include_router(publico.router)
app.include_router(asociaciones.router)
app.include_router(productos.router)

# Para que los routers puedan usar templates, los exponemos
# Opcional: puedes pasar templates a los routers como dependencia, pero lo más simple es importar app en cada router.
# En cada router, haz: from ..main import templates