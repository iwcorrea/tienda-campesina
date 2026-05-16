import logging
import os
from fastapi import FastAPI, Request, APIRouter
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base, SessionLocal
from app.models import Configuracion
import cloudinary
import time
from sqlalchemy import text

# EventDispatcher
from app.events.dispatcher import EventDispatcher
from app.events.registry import register_all_listeners
from app.modules.orders.events import init_dispatcher

# Routers v2 modulares
from app.modules.auth import router_v2 as auth_v2
from app.modules.users import router_v2 as users_v2
from app.modules.orders import router_v2 as orders_v2
from app.modules.transport import router_v2 as transport_v2
from app.modules.products import router_v2 as products_v2
from app.modules.dashboard import router_v2 as dashboard_v2
from app.modules.admin import router_v2 as admin_v2

logging.basicConfig(level=logging.INFO)

app = FastAPI()

cloudinary.config(cloudinary_url=os.getenv("CLOUDINARY_URL"))
SECRET_KEY = os.getenv("SECRET_KEY", "dev_key")

# ─── Exception handler ────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Error no manejado: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Error interno del servidor"})

# ─── Middlewares ───────────────────────────────────
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
            return JSONResponse(status_code=401, content={"detail": "Sesión expirada"})
        request.session["last_activity"] = now
    response = await call_next(request)
    return response

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, same_site="lax", https_only=True)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ─── EventDispatcher ──────────────────────────────
dispatcher = EventDispatcher()
init_dispatcher(dispatcher)
register_all_listeners(dispatcher)

# ─── Routers API v2 ───────────────────────────────
v2_modular_router = APIRouter(prefix="/api/v2/modular")
v2_modular_router.include_router(auth_v2.router, prefix="/auth", tags=["auth_v2"])
v2_modular_router.include_router(users_v2.router, prefix="/users", tags=["users_v2"])
v2_modular_router.include_router(orders_v2.router, prefix="/orders", tags=["orders_v2"])
v2_modular_router.include_router(transport_v2.router, prefix="/transport", tags=["transport_v2"])
v2_modular_router.include_router(products_v2.router, prefix="/products", tags=["products_v2"])
v2_modular_router.include_router(dashboard_v2.router, prefix="/dashboard", tags=["dashboard_v2"])
v2_modular_router.include_router(admin_v2.router, prefix="/admin", tags=["admin_v2"])
app.include_router(v2_modular_router)

# ─── Frontend React (SPA) ─────────────────────────
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))

if os.path.isdir(FRONTEND_DIR):
    # Montar assets estáticos (JS, CSS)
    assets_dir = os.path.join(FRONTEND_DIR, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    # Servir index.html como fallback para todas las rutas no capturadas
    @app.get("/{full_path:path}", response_class=FileResponse)
    async def serve_spa(full_path: str):
        """
        Sirve archivos estáticos del frontend o el index.html (SPA).
        """
        file_path = os.path.join(FRONTEND_DIR, full_path) if full_path else None
        if file_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        # Fallback SPA
        index_path = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return JSONResponse(status_code=404, content={"detail": "Not found"})
else:
    @app.get("/")
    async def no_frontend():
        return JSONResponse({"detail": "Frontend no construido"}, status_code=500)

# ─── Startup ──────────────────────────────────────
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        existing = set()
        rows = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='configuracion'"))
        for row in rows:
            existing.add(row[0])
        if "permitir_registro" not in existing:
            conn.execute(text("ALTER TABLE configuracion ADD COLUMN permitir_registro BOOLEAN DEFAULT TRUE"))
        if "mantenimiento_modo" not in existing:
            conn.execute(text("ALTER TABLE configuracion ADD COLUMN mantenimiento_modo BOOLEAN DEFAULT FALSE"))
        for tabla in ["asociaciones", "personas", "transportistas", "pedidos", "transportes"]:
            cols = conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name='{tabla}'"))
            col_names = {row[0] for row in cols}
            if "region" not in col_names:
                conn.execute(text(f"ALTER TABLE {tabla} ADD COLUMN region VARCHAR DEFAULT NULL"))
        conn.commit()