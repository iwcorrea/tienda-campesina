import logging
import os
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.auth import router as auth_router
from app.database import engine, Base, SessionLocal
from app.models import Configuracion
from app.templates import templates
from app.cloudinary_utils import delete_cloudinary_asset
import cloudinary
import time
from sqlalchemy import text

# Routers
from app.routers import home, catalogo, dashboard, panel, perfil, asociacion, valoraciones, admin, calculadora
from app.routers import personas, empleos, herramientas, mensajes
from app.routers import transportistas
from app.routers import pedidos
from app.routers import carrito
from app.routers import ayuda
from app.routers import noticias
from app.routers import notificaciones
from app.routers import contactos
from app.routers import transportista_envios
from app.routers import pagos

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

    # Control de inactividad (solo si la sesión tiene usuario y last_activity)
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

app.include_router(auth_router, prefix="/auth")
app.include_router(home.router)
app.include_router(catalogo.router)
app.include_router(dashboard.router)
app.include_router(panel.router)
app.include_router(perfil.router)
app.include_router(asociacion.router)
app.include_router(valoraciones.router)
app.include_router(admin.router)
app.include_router(calculadora.router)
app.include_router(personas.router)
app.include_router(empleos.router)
app.include_router(herramientas.router)
app.include_router(mensajes.router)
app.include_router(transportistas.router)
app.include_router(pedidos.router)
app.include_router(carrito.router)
app.include_router(ayuda.router)
app.include_router(noticias.router)
app.include_router(notificaciones.router)
app.include_router(contactos.router)
app.include_router(transportista_envios.router)
app.include_router(pagos.router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        # Configuracion
        existing = set()
        rows = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='configuracion'"))
        for row in rows:
            existing.add(row[0])
        model_columns = Configuracion.__table__.columns
        for col in model_columns:
            if col.name not in existing:
                col_type = col.type.compile(dialect=engine.dialect)
                sql = f'ALTER TABLE configuracion ADD COLUMN IF NOT EXISTS {col.name} {col_type}'
                conn.execute(text(sql))

        # Asociaciones
        existing_asoc = set()
        rows_asoc = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='asociaciones'"))
        for row in rows_asoc:
            existing_asoc.add(row[0])
        for col_name in ["pregunta_secreta", "respuesta_secreta_hash"]:
            if col_name not in existing_asoc:
                sql = f'ALTER TABLE asociaciones ADD COLUMN IF NOT EXISTS {col_name} TEXT DEFAULT \'\''
                conn.execute(text(sql))

        # Personas
        existing_pers = set()
        rows_pers = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='personas'"))
        for row in rows_pers:
            existing_pers.add(row[0])
        for col_name in ["pregunta_secreta", "respuesta_secreta_hash"]:
            if col_name not in existing_pers:
                sql = f'ALTER TABLE personas ADD COLUMN IF NOT EXISTS {col_name} TEXT DEFAULT \'\''
                conn.execute(text(sql))

        # Transportistas
        existing_trans = set()
        rows_trans = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='transportistas'"))
        if rows_trans.rowcount > 0:
            for row in rows_trans:
                existing_trans.add(row[0])
            for col_name in ["documento_url"]:
                if col_name not in existing_trans:
                    sql = f'ALTER TABLE transportistas ADD COLUMN IF NOT EXISTS {col_name} TEXT DEFAULT \'\''
                    conn.execute(text(sql))

        # Vacantes
        existing_vac = set()
        rows_vac = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='vacantes'"))
        for row in rows_vac:
            existing_vac.add(row[0])
        for col_name, col_type in [
            ("tipo_contrato", "TEXT DEFAULT 'termino_fijo'"),
            ("jornada", "TEXT DEFAULT 'completa'"),
            ("requisitos", "TEXT DEFAULT ''"),
            ("terminos_url", "TEXT DEFAULT ''")
        ]:
            if col_name not in existing_vac:
                sql = f'ALTER TABLE vacantes ADD COLUMN IF NOT EXISTS {col_name} {col_type}'
                conn.execute(text(sql))

        # RespuestasCotizacion (contrato_url, factura_url)
        existing_resp = set()
        rows_resp = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='respuestas_cotizaciones'"))
        for row in rows_resp:
            existing_resp.add(row[0])
        for col_name in ["contrato_url", "factura_url"]:
            if col_name not in existing_resp:
                sql = f'ALTER TABLE respuestas_cotizaciones ADD COLUMN IF NOT EXISTS {col_name} TEXT DEFAULT \'\''
                conn.execute(text(sql))

        # Pedidos (transportista_id, estado_envio, costo_envio)
        existing_ped = set()
        rows_ped = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='pedidos'"))
        for row in rows_ped:
            existing_ped.add(row[0])
        for col_name in ["transportista_id", "estado_envio", "costo_envio"]:
            if col_name not in existing_ped:
                sql = f'ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS {col_name} TEXT DEFAULT \'\''
                conn.execute(text(sql))

        # Pagos (nueva tabla)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS pagos (
                id VARCHAR PRIMARY KEY,
                pedido_id VARCHAR NOT NULL REFERENCES pedidos(id),
                comprador_email VARCHAR NOT NULL,
                monto_total INTEGER NOT NULL,
                comision_plataforma INTEGER NOT NULL,
                monto_vendedor INTEGER NOT NULL,
                estado VARCHAR DEFAULT 'pendiente',
                wompi_transaccion_id VARCHAR,
                wompi_referencia VARCHAR,
                fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                fecha_confirmacion TIMESTAMP WITH TIME ZONE
            )
        """))

        # Comisiones (nueva tabla)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS comisiones (
                id VARCHAR PRIMARY KEY,
                pago_id VARCHAR NOT NULL REFERENCES pagos(id),
                pedido_id VARCHAR NOT NULL REFERENCES pedidos(id),
                asociacion_email VARCHAR NOT NULL REFERENCES asociaciones(email),
                comprador_email VARCHAR NOT NULL,
                monto_venta INTEGER NOT NULL,
                porcentaje_comision INTEGER NOT NULL,
                monto_comision INTEGER NOT NULL,
                fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))

        # MovimientosInventario (nueva tabla)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS movimientos_inventario (
                id VARCHAR PRIMARY KEY,
                producto_id VARCHAR NOT NULL REFERENCES productos(id),
                asociacion_email VARCHAR NOT NULL REFERENCES asociaciones(email),
                tipo VARCHAR NOT NULL,
                cantidad INTEGER NOT NULL,
                stock_anterior INTEGER DEFAULT 0,
                stock_nuevo INTEGER DEFAULT 0,
                referencia VARCHAR DEFAULT '',
                fecha TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))

        # ValoracionesComprador (nueva tabla)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS valoraciones_compradores (
                id VARCHAR PRIMARY KEY,
                comprador_email VARCHAR NOT NULL,
                asociacion_email VARCHAR NOT NULL,
                pedido_id VARCHAR NOT NULL,
                estrellas INTEGER NOT NULL,
                comentario TEXT DEFAULT '',
                fecha TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                FOREIGN KEY (asociacion_email) REFERENCES asociaciones(email),
                FOREIGN KEY (pedido_id) REFERENCES pedidos(id)
            )
        """))

        # SolicitudesContacto (nueva tabla)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS solicitudes_contacto (
                id VARCHAR PRIMARY KEY,
                solicitante_email VARCHAR NOT NULL,
                receptor_email VARCHAR NOT NULL,
                estado VARCHAR DEFAULT 'pendiente',
                fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))

        # Bloqueos (nueva tabla)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS bloqueos (
                id VARCHAR PRIMARY KEY,
                bloqueador_email VARCHAR NOT NULL,
                bloqueado_email VARCHAR NOT NULL,
                fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))

        # NotificacionesSistema (nueva tabla)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS notificaciones_sistema (
                id VARCHAR PRIMARY KEY,
                destinatario_email VARCHAR NOT NULL,
                texto TEXT NOT NULL,
                leido VARCHAR DEFAULT '0',
                fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                url TEXT DEFAULT ''
            )
        """))

        # Contactos (nueva tabla)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS contactos (
                id VARCHAR PRIMARY KEY,
                usuario_email VARCHAR NOT NULL,
                contacto_email VARCHAR NOT NULL,
                tipo_relacion VARCHAR DEFAULT 'contacto',
                fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))

        # Productos (columna stock)
        existing_prod = set()
        rows_prod = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='productos'"))
        for row in rows_prod:
            existing_prod.add(row[0])
        if "stock" not in existing_prod:
            conn.execute(text("ALTER TABLE productos ADD COLUMN stock INTEGER DEFAULT 0"))

        conn.commit()