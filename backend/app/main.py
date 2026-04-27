import logging
import os
import uuid
from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.auth import router as auth_router
from app.google_sheets import get_sheet, get_products_sheet
import cloudinary
import cloudinary.uploader
import datetime

logging.basicConfig(level=logging.INFO)

app = FastAPI()

cloudinary.config(cloudinary_url=os.getenv("CLOUDINARY_URL"))

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

# ─── CATÁLOGO (con logos, enlaces a perfil) ─────────────
@app.get("/catalogo", response_class=HTMLResponse)
def catalogo(request: Request):
    try:
        sheet_prod = get_products_sheet()
        registros = sheet_prod.get_all_values()
        datos = registros[1:] if len(registros) > 1 else []
        logging.info(f"Catálogo: {len(datos)} filas de productos")
    except Exception as e:
        logging.exception("Error al leer hoja Productos")
        datos = []

    logos = {}
    nombres_asoc = {}
    try:
        sheet_usr = get_sheet()
        usuarios = sheet_usr.get_all_values()[1:]
        for u in usuarios:
            if u[0]:
                logos[u[0].strip()] = u[7].strip() if len(u) > 7 and u[7].strip() else ""
                nombres_asoc[u[0].strip()] = u[3].strip() if len(u) > 3 and u[3].strip() else u[0]
    except Exception as e:
        logging.exception("Error al leer logos de usuarios")

    productos = []
    for fila in datos:
        if len(fila) >= 2 and fila[0].strip():
            email_asoc = fila[0].strip()
            # Nuevas columnas: tipo (índice 7), tipo_precio (8)
            tipo = fila[7].strip() if len(fila) > 7 else ""
            tipo_precio = fila[8].strip() if len(fila) > 8 else ""
            productos.append({
                "id": fila[0] if len(fila) > 0 else "",
                "nombre": fila[1] if len(fila) > 1 else "",
                "descripcion": fila[2] if len(fila) > 2 else "",
                "precio": fila[3] if len(fila) > 3 else "",
                "imagen": fila[4].strip() if len(fila) > 4 and fila[4].strip() else "https://placehold.co/300x200/5B8C51/white?text=Producto",
                "asociacion": email_asoc,
                "asociacion_nombre": nombres_asoc.get(email_asoc, email_asoc),
                "logo_url": logos.get(email_asoc, ""),
                "tipo": tipo,
                "tipo_precio": tipo_precio
            })
    logging.info(f"Catálogo: {len(productos)} productos listos")
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
        mis_productos = [fila for fila in datos if fila[1] == email]  # email ahora en columna B
    except Exception:
        mis_productos = []

    productos_obj = []
    for p in mis_productos:
        productos_obj.append({
            "id": p[0] if len(p) > 0 else "",
            "nombre": p[2] if len(p) > 2 else "",
            "descripcion": p[3] if len(p) > 3 else "",
            "precio": p[4] if len(p) > 4 else "",
            "imagen": p[5] if len(p) > 5 else "",
            "tipo": p[7] if len(p) > 7 else "",
            "tipo_precio": p[8] if len(p) > 8 else ""
        })

    return templates.TemplateResponse("panel.html", {
        "request": request,
        "usuario": request.session.get("nombre_asociacion", email),
        "productos": productos_obj
    })

# ─── CREAR PRODUCTO (con ID, tipo y tipo_precio) ─────
@app.post("/panel/producto")
def crear_producto(
    request: Request,
    nombre: str = Form(...),
    descripcion: str = Form(None),
    precio: int = Form(...),
    tipo: str = Form("producto"),       # "producto" o "servicio"
    tipo_precio: str = Form("fijo"),    # "fijo" o "convenir"
    imagen: UploadFile = File(None)
):
    if "usuario" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=303)

    email = request.session["usuario"]
    producto_id = str(uuid.uuid4())
    imagen_url = ""

    if imagen and imagen.filename:
        try:
            result = cloudinary.uploader.upload(imagen.file, folder="productos")
            imagen_url = result.get("secure_url", "")
        except Exception as e:
            logging.exception("Error subiendo imagen a Cloudinary")

    try:
        sheet_prod = get_products_sheet()
        # Asegurar encabezados (ya los tiene get_products_sheet)
        sheet_prod.append_row([
            producto_id,
            email,
            nombre,
            descripcion or "",
            precio,
            imagen_url,
            str(datetime.datetime.now()),
            tipo,
            tipo_precio
        ])
    except Exception as e:
        logging.exception("Error al guardar producto en Sheets")

    return RedirectResponse(url="/panel", status_code=303)

# ─── EDITAR PRODUCTO (formulario) ───────────────────
@app.get("/panel/producto/editar/{producto_id}", response_class=HTMLResponse)
def editar_producto_form(request: Request, producto_id: str):
    if "usuario" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=303)

    email = request.session["usuario"]
    try:
        sheet_prod = get_products_sheet()
        todos = sheet_prod.get_all_values()[1:]
        for i, fila in enumerate(todos):
            if fila[0] == producto_id and fila[1] == email:
                producto = {
                    "id": fila[0],
                    "nombre": fila[2],
                    "descripcion": fila[3] if len(fila) > 3 else "",
                    "precio": fila[4] if len(fila) > 4 else "",
                    "imagen_url": fila[5] if len(fila) > 5 else "",
                    "tipo": fila[7] if len(fila) > 7 else "producto",
                    "tipo_precio": fila[8] if len(fila) > 8 else "fijo"
                }
                return templates.TemplateResponse("editar_producto.html", {"request": request, "producto": producto})
        return RedirectResponse(url="/panel", status_code=303)
    except Exception as e:
        logging.exception("Error al obtener producto para editar")
        return RedirectResponse(url="/panel", status_code=303)

# ─── ACTUALIZAR PRODUCTO ───────────────────────────
@app.post("/panel/producto/actualizar/{producto_id}")
def actualizar_producto(
    request: Request,
    producto_id: str,
    nombre: str = Form(...),
    descripcion: str = Form(None),
    precio: int = Form(...),
    tipo: str = Form("producto"),
    tipo_precio: str = Form("fijo"),
    imagen: UploadFile = File(None)
):
    if "usuario" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=303)

    email = request.session["usuario"]
    try:
        sheet_prod = get_products_sheet()
        todos = sheet_prod.get_all_values()
        # Encontrar fila por ID y email
        for i, fila in enumerate(todos):
            if i == 0:  # skip headers
                continue
            if fila[0] == producto_id and fila[1] == email:
                # Mantener la imagen antigua si no se sube nueva
                nueva_imagen = fila[5] if len(fila) > 5 else ""
                if imagen and imagen.filename:
                    try:
                        result = cloudinary.uploader.upload(imagen.file, folder="productos")
                        nueva_imagen = result.get("secure_url", "")
                    except Exception as e:
                        logging.exception("Error al actualizar imagen en Cloudinary")

                # Actualizar fila (columnas: id, email, nombre, desc, precio, img, fecha, tipo, tipo_precio)
                sheet_prod.update(f'A{i+1}:I{i+1}', [[
                    producto_id,
                    email,
                    nombre,
                    descripcion or "",
                    precio,
                    nueva_imagen,
                    fila[6] if len(fila) > 6 else str(datetime.datetime.now()),
                    tipo,
                    tipo_precio
                ]])
                break
        return RedirectResponse(url="/panel", status_code=303)
    except Exception as e:
        logging.exception("Error al actualizar producto")
        return RedirectResponse(url="/panel", status_code=303)

# ─── ELIMINAR PRODUCTO ─────────────────────────────
@app.post("/panel/producto/eliminar/{producto_id}")
def eliminar_producto(request: Request, producto_id: str):
    if "usuario" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=303)

    email = request.session["usuario"]
    try:
        sheet_prod = get_products_sheet()
        todos = sheet_prod.get_all_values()
        for i, fila in enumerate(todos):
            if i == 0:
                continue
            if fila[0] == producto_id and fila[1] == email:
                sheet_prod.delete_rows(i + 1)  # i + 1 porque sheets empieza en 1
                break
    except Exception as e:
        logging.exception("Error al eliminar producto")
    return RedirectResponse(url="/panel", status_code=303)

# ─── PERFIL PÚBLICO DE ASOCIACIÓN ─────────────────
@app.get("/asociacion/{email}", response_class=HTMLResponse)
def perfil_asociacion(request: Request, email: str):
    # Obtener datos de la asociación desde hoja de usuarios
    asociacion = None
    try:
        sheet_usr = get_sheet()
        usuarios = sheet_usr.get_all_values()[1:]
        for u in usuarios:
            if u[0] == email:
                asociacion = {
                    "email": u[0],
                    "nombre": u[3] if len(u) > 3 else u[0],
                    "descripcion": u[4] if len(u) > 4 else "",
                    "direccion": u[5] if len(u) > 5 else "",
                    "telefono": u[6] if len(u) > 6 else "",
                    "logo_url": u[7].strip() if len(u) > 7 and u[7].strip() else ""
                }
                break
    except Exception as e:
        logging.exception("Error al leer asociación")

    if not asociacion:
        return RedirectResponse(url="/catalogo", status_code=303)

    # Obtener productos de esa asociación
    productos = []
    try:
        sheet_prod = get_products_sheet()
        todos = sheet_prod.get_all_values()[1:]
        for fila in todos:
            if fila[1] == email:
                productos.append({
                    "nombre": fila[2],
                    "descripcion": fila[3] if len(fila) > 3 else "",
                    "precio": fila[4] if len(fila) > 4 else "",
                    "imagen": fila[5].strip() if len(fila) > 5 and fila[5].strip() else "https://placehold.co/300x200/5B8C51/white?text=Producto",
                    "tipo": fila[7] if len(fila) > 7 else "",
                    "tipo_precio": fila[8] if len(fila) > 8 else ""
                })
    except Exception as e:
        logging.exception("Error al leer productos de la asociación")

    return templates.TemplateResponse("perfil.html", {
        "request": request,
        "asociacion": asociacion,
        "productos": productos
    })