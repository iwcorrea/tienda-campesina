import logging
import os
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as users_router
from app.modules.products.router import router as products_router
from app.modules.orders.router import router as orders_router
from app.modules.notifications.router import router as notifications_router
from app.database import engine, Base, SessionLocal
from app.models import Configuracion
from app.templates import templates
from app.cloudinary_utils import delete_cloudinary_asset
import cloudinary
import time
from sqlalchemy import text

# Routers legacy que aún no se migran
from app.routers import home, dashboard, admin, calculadora
from app.routers import empleos, herramientas
from app.routers import ayuda
from app.routers import noticias

logging.basicConfig(level=logging.INFO)

app = FastAPI()

cloudinary.config(cloudinary_url=os.getenv("CLOUDINARY_URL"))

SECRET_KEY = os.getenv("SECRET_KEY", "dev_key")

# ─── MANEJO GLOBAL DE ERRORES ──
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Error no manejado: {exc}", exc_info=True)
    return HTMLResponse(
        content=templates.get_template("500.html").render({"request": request}),
        status_code=500
    )

# ─── MIDDLEWARE COMBINADO ──
@app.middleware("http")
async def timeout_y_configuracion(request: Request, call_next):
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

    if "usuario" in request.session and "last_activity" in request.session:
        last_activity = request.session["last_activity"]
        now = time.time()
        if now - last_activity > 300:
            request.session.clear()
            return RedirectResponse(url="/auth/login", status_code=303)
        request.session["last_activity"] = now

    response = await call_next(request)
    return response

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, same_site="lax", https_only=True)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ─── Routers ──────────────────────────────────────
app.include_router(auth_router, prefix="/auth")
app.include_router(users_router)
app.include_router(products_router)
app.include_router(orders_router)
app.include_router(notifications_router)
app.include_router(home.router)
app.include_router(dashboard.router)
app.include_router(admin.router)
app.include_router(calculadora.router)
app.include_router(empleos.router)
app.include_router(herramientas.router)
app.include_router(ayuda.router)
app.include_router(noticias.router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        # ... (todas las migraciones anteriores se mantienen igual) ...

        # Notificaciones (nueva tabla)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS notificaciones (
                id VARCHAR PRIMARY KEY,
                usuario_email VARCHAR NOT NULL,
                tipo_evento VARCHAR NOT NULL,
                canal VARCHAR DEFAULT 'in_app',
                estado VARCHAR DEFAULT 'pending',
                titulo TEXT DEFAULT '',
                contenido TEXT DEFAULT '',
                referencia_pedido_id VARCHAR,
                fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                fecha_envio TIMESTAMP WITH TIME ZONE,
                fecha_lectura TIMESTAMP WITH TIME ZONE
            )
        """))

        conn.commit()