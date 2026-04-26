import logging
from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
import os
from app.auth import router as auth_router
from app.google_sheets import get_sheet, get_products_sheet, upload_to_gcs
import datetime

logging.basicConfig(level=logging.INFO)

app = FastAPI()

SECRET_KEY = os.getenv("SECRET_KEY", "dev_key")
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="lax",
    https_only=True,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(auth_router, prefix="/auth")

# ─── HOME ───────────────────────────────────────────────
@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
def inicio(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ─── MENÚ ──────────────────────────────────────────────
@app.get("/menu", response_class=HTMLResponse)
def menu(request: Request):
    return templates.TemplateResponse("menu.html", {"request": request})

# ─── CATÁLOGO (mejorado con logs y validación de columnas) ─
@app.get("/catalogo", response_class=HTMLResponse)
def catalogo(request: Request):
    try:
        sheet_prod = get_products_sheet()
        registros = sheet_prod.get_all_values()
        if len(registros) > 1:
            datos = registros[1:]  # sin encabezados
        else:
            datos = []
        logging.info(f"Catálogo: {len(datos)} filas encontradas en Productos")
    except Exception as e:
        logging.exception("Error al leer la hoja Productos")
        datos = []

    productos = []
    for fila in datos:
        # Solo procesar filas con al menos email y nombre
        if len(fila) >= 2 and fila[0].strip():
            productos.append({
                "nombre": fila[1] if len(fila) > 1 else "",
                "descripcion": fila[2] if len(fila) > 2 else "",
                "precio": fila[3] if len(fila) > 3 else "",
                "imagen": (fila[4].strip() if len(fila) > 4 and fila[4].strip() else
                           "https://placehold.co/300x200/5B8C51/white?text=Producto"),
                "asociacion": fila[0]
            })
    logging.info(f"Catálogo: {len(productos)} productos listos para mostrar")
    return templates.TemplateResponse("catalogo.html", {"request": request, "productos": productos})

# ─── PANEL (protegido) ───────────────────────────────
@app.get("/panel", response_class=HTMLResponse)
def panel(request: Request):
    if "usuario" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=303)

    email = request.session["usuario"]
    try:
        sheet_prod = get_products_sheet()
        todos = sheet_prod.get_all_values()
        datos = todos[1:] if len(todos) > 1 else []
        mis_productos = [fila for fila in datos if fila[0] == email]
    except Exception:
        mis_productos = []

    productos_obj = []
    for p in mis_productos:
        productos_obj.append({
            "nombre": p[1] if len(p) > 1 else "",
            "descripcion": p[2] if len(p) > 2 else "",
            "precio": p[3] if len(p) > 3 else "",
            "imagen": p[4] if len(p) > 4 else ""
        })

    return templates.TemplateResponse("panel.html", {
        "request": request,
        "usuario": request.session.get("nombre_asociacion", email),
        "productos": productos_obj
    })

# ─── CREAR PRODUCTO (acepta imagen) ─────────────────
@app.post("/panel/producto")
def crear_producto(
    request: Request,
    nombre: str = Form(...),
    descripcion: str = Form(None),
    precio: int = Form(...),
    imagen: UploadFile = File(None)
):
    if "usuario" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=303)

    email = request.session["usuario"]
    imagen_url = ""

    if imagen and imagen.filename:
        try:
            imagen_url = upload_to_gcs(imagen, imagen.filename, folder="productos")
        except Exception as e:
            logging.exception("Error subiendo imagen a GCS")

    try:
        sheet_prod = get_products_sheet()
        # Agregar los encabezados si la hoja está vacía (primera fila vacía o no tiene encabezados)
        todos = sheet_prod.get_all_values()
        if not todos or not any(todos[0]):
            sheet_prod.append_row(["email", "nombre", "descripcion", "precio", "imagen_url", "fecha"])
        sheet_prod.append_row([
            email,
            nombre,
            descripcion or "",
            precio,
            imagen_url,
            str(datetime.datetime.now())
        ])
    except Exception as e:
        logging.exception("Error al guardar producto en Sheets")

    return RedirectResponse(url="/panel", status_code=303)