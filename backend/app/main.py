from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from .database import engine
from . import models
from .dependencies import templates
from .routers import auth, publico, asociaciones, productos

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.include_router(auth.router)
app.include_router(publico.router)
app.include_router(asociaciones.router)
app.include_router(productos.router)