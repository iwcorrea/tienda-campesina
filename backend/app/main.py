from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import os

from app.auth import router as auth_router

app = FastAPI()

# 🔐 SECRET KEY
SECRET_KEY = os.getenv("SECRET_KEY", "dev_key")

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="lax",
    https_only=True,
)

# 🔥 STATIC (CSS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 🔥 TEMPLATES
templates = Jinja2Templates(directory="app/templates")

# 🔥 ROUTERS
app.include_router(auth_router, prefix="/auth")


# 🔥 HOME → REDIRECT
@app.get("/")
def home():
    return RedirectResponse(url="/menu")


# 🔥 MENÚ (AHORA CON TEMPLATE REAL)
@app.get("/menu", response_class=HTMLResponse)
def menu(request: Request):
    return templates.TemplateResponse("menu.html", {"request": request})


# 🔥 CATÁLOGO
@app.get("/catalogo", response_class=HTMLResponse)
def catalogo(request: Request):
    return templates.TemplateResponse("catalogo.html", {"request": request})