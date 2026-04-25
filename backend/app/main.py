from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import models
from .database import engine
from .routers.asociaciones import router as asociaciones_router
from .routers.auth import router as auth_router
from .routers.productos import router as productos_router
from .routers.publico import router as publico_router

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent / ".env")

app = FastAPI(title="Asociaciones de Productores Campesinos")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.state.templates = templates

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Configuracion CORS basica para despliegues web separados.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crea las tablas al iniciar la aplicacion.
models.Base.metadata.create_all(bind=engine)

app.include_router(publico_router, prefix="")
app.include_router(auth_router, prefix="")
app.include_router(asociaciones_router, prefix="")
app.include_router(productos_router, prefix="")


@app.get("/inicio", include_in_schema=False)
def root_redirect():
    return RedirectResponse(url="/", status_code=307)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return templates.TemplateResponse(
            "404.html",
            {"request": request},
            status_code=404,
        )
    raise exc


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return templates.TemplateResponse(
        "404.html",
        {"request": request},
        status_code=404,
    )
