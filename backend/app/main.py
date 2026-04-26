from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
import os

from app.routes import router as main_router
from app.auth import router as auth_router

app = FastAPI()

# 🔐 Clave secreta obligatoria
SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise ValueError("Falta configurar SECRET_KEY en variables de entorno")

# 🚀 Middleware de sesión (CORREGIDO)
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="lax",
    https_only=True,
    max_age=60 * 60 * 24  # 1 día
)

# 📦 Rutas
app.include_router(main_router)
app.include_router(auth_router, prefix="/auth")

# 🧪 Ruta base
@app.get("/")
def home():
    return {"status": "ok"}