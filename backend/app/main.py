import logging
import os
from fastapi import FastAPI, Request, APIRouter
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware

from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as users_router
from app.modules.products.router import router as products_router
from app.modules.orders.router import router as orders_router
from app.modules.notifications.router import router as notifications_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.matching.router import router as matching_router

from app.database import engine, Base, SessionLocal
from app.models import Configuracion
from app.templates import templates
from app.cloudinary_utils import delete_cloudinary_asset
import cloudinary
import time
from sqlalchemy import text

# Routers legacy
from app.routers import home, admin, calculadora
from app.routers import empleos, herramientas
from app.routers import ayuda
from app.routers import noticias

# EventDispatcher
from app.events.dispatcher import EventDispatcher
from app.events.registry import register_all_listeners
from app.modules.orders.events import init_dispatcher

# Routers v2 modulares
from app.modules.orders import router_v2 as orders_v2
from app.modules.transport import router_v2 as transport_v2
from app.modules.products import router_v2 as products_v2
from app.modules.dashboard import router_v2 as dashboard_v2
from app.modules.admin import router_v2 as admin_v2
from app.modules.auth import router_v2 as auth_v2
from app.modules.users import router_v2 as users_v2

logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Configuraciones previas
cloudinary.config(cloudinary_url=os.getenv("CLOUDINARY_URL"))
SECRET_KEY = os.getenv("SECRET_KEY", "dev_key")

# Middlewares
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Error no manejado: {exc}", exc_info=True)
    return HTMLResponse(
        content=templates.get_template("500.html").render({"request": request}),
        status_code=500
    )

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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Inicialización del EventDispatcher central
dispatcher = EventDispatcher()
init_dispatcher(dispatcher)
register_all_listeners(dispatcher)

# Función que registra TODOS los routers legacy
def include_legacy_routers(target_app: FastAPI):
    target_app.include_router(auth_router, prefix="/auth")
    target_app.include_router(users_router)
    target_app.include_router(products_router)
    target_app.include_router(orders_router)
    target_app.include_router(notifications_router)
    target_app.include_router(dashboard_router)
    target_app.include_router(matching_router)
    target_app.include_router(home.router)
    target_app.include_router(admin.router)
    target_app.include_router(calculadora.router)
    target_app.include_router(empleos.router)
    target_app.include_router(herramientas.router)
    target_app.include_router(ayuda.router)
    target_app.include_router(noticias.router)

# Aplicación principal (rutas legacy en raíz)
include_legacy_routers(app)

# Sub-aplicación para API v1
v1_app = FastAPI(title="API v1 (Legacy)", description="Endpoints legacy", version="1.0.0")
include_legacy_routers(v1_app)
app.mount("/api/v1", v1_app)

# Enrutador v2 modular
v2_modular_router = APIRouter(prefix="/api/v2/modular")
v2_modular_router.include_router(orders_v2.router, prefix="/orders", tags=["orders_v2"])
v2_modular_router.include_router(transport_v2.router, prefix="/transport", tags=["transport_v2"])
v2_modular_router.include_router(products_v2.router, prefix="/products", tags=["products_v2"])
v2_modular_router.include_router(dashboard_v2.router, prefix="/dashboard", tags=["dashboard_v2"])
v2_modular_router.include_router(admin_v2.router, prefix="/admin", tags=["admin_v2"])
v2_modular_router.include_router(auth_v2.router, prefix="/auth", tags=["auth_v2"])
v2_modular_router.include_router(users_v2.router, prefix="/users", tags=["users_v2"])
app.include_router(v2_modular_router)

# Startup
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        # Asegurar columnas en configuracion
        existing = set()
        rows = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='configuracion'"))
        for row in rows:
            existing.add(row[0])
        if "permitir_registro" not in existing:
            conn.execute(text("ALTER TABLE configuracion ADD COLUMN permitir_registro BOOLEAN DEFAULT TRUE"))
        if "mantenimiento_modo" not in existing:
            conn.execute(text("ALTER TABLE configuracion ADD COLUMN mantenimiento_modo BOOLEAN DEFAULT FALSE"))

        # Agregar columna region a las tablas principales si no existe
        for tabla in ["asociaciones", "personas", "transportistas", "pedidos", "transportes"]:
            cols = conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name='{tabla}'"))
            col_names = {row[0] for row in cols}
            if "region" not in col_names:
                conn.execute(text(f"ALTER TABLE {tabla} ADD COLUMN region VARCHAR DEFAULT NULL"))
        conn.commit()
