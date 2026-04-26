from fastapi import FastAPI
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
import os

from app.auth import router as auth_router

app = FastAPI()

SECRET_KEY = os.getenv("SECRET_KEY", "dev_key")

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="lax",
    https_only=True,
)

app.include_router(auth_router, prefix="/auth")

# 🔥 REDIRECCIÓN PRINCIPAL
@app.get("/")
def home():
    return RedirectResponse(url="/menu")


# 🔥 MENÚ PRINCIPAL (INTERFAZ SIMPLE)
@app.get("/menu", response_class=HTMLResponse)
def menu():
    return """
    <h1>Tienda Campesina</h1>
    <ul>
        <li><a href="/auth/login">Login</a></li>
        <li><a href="/auth/registro">Registro</a></li>
        <li><a href="/catalogo">Ver Catálogo</a></li>
    </ul>
    """


# 🔥 CATÁLOGO SIMPLE
@app.get("/catalogo", response_class=HTMLResponse)
def catalogo():
    return """
    <h2>Catálogo de Productos</h2>
    <p>Aquí irán los productos</p>
    <a href="/menu">Volver</a>
    """