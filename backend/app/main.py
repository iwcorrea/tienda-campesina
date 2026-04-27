import logging
import os
import uuid
from fastapi import FastAPI, Request, Form, File, UploadFile, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.auth import router as auth_router
from app.google_sheets import get_sheet, get_products_sheet, get_valoraciones_sheet
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

def delete_cloudinary_asset(url: str, resource_type: str = "image"):
    if not url or "cloudinary.com" not in url:
        return
    try:
        parts = url.split("/")
        upload_idx = -1
        for i, part in enumerate(parts):
            if part == "upload":
                upload_idx = i
                break
        if upload_idx == -1 or upload_idx + 2 >= len(parts):
            return
        public_id_with_ext = "/".join(parts[upload_idx + 2:])
        public_id = ".".join(public_id_with_ext.split(".")[:-1])
        result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        logging.info(f"Eliminado recurso antiguo: {public_id} -> {result}")
    except Exception as e:
        logging.exception("Error al eliminar recurso antiguo de Cloudinary")

# ─── HOME ───────────────────────────────────────────────
@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
def inicio(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ─── MENÚ ──────────────────────────────────────────────
@app.get("/menu", response_class=HTMLResponse)
def menu(request: Request):
    return templates.TemplateResponse("menu.html", {"request": request})

# ─── CATÁLOGO ─────────────────────────────────────────
@app.get("/catalogo", response_class=HTMLResponse)
def catalogo(
    request: Request,
    q: str = Query(default=None),
    tipo: str = Query(default=None),
    tipo_precio: str = Query(default=None),
    page: int = Query(default=1, ge=1)
):
    try:
        sheet_prod = get_products_sheet()
        registros = sheet_prod.get_all_values()
        datos = registros[1:] if len(registros) > 1 else []
    except Exception:
        datos = []

    logos = {}
    nombres_asoc = {}
    whatsapp_info = {}
    verificados = set()
    try:
        sheet_usr = get_sheet()
        usuarios = sheet_usr.get_all_values()[1:]
        for u in usuarios:
            if u[0]:
                email_usr = u[0].strip()
                logos[email_usr] = u[7].strip() if len(u) > 7 and u[7].strip() else ""
                nombres_asoc[email_usr] = u[3].strip() if len(u) > 3 and u[3].strip() else email_usr
                whatsapp_info[email_usr] = {
                    "show_whatsapp": u[8].strip() if len(u) > 8 and u[8].strip() else "",
                    "telefono": u[6].strip() if len(u) > 6 and u[6].strip() else ""
                }
                if len(u) > 11 and u[11].strip() == "1":
                    verificados.add(email_usr)
    except Exception:
        pass

    valoraciones = {}
    try:
        sheet_val = get_valoraciones_sheet()
        vals = sheet_val.get_all_values()[1:]
        for v in vals:
            pid = v[1].strip() if len(v) > 1 else ""
            estrellas = int(v[2]) if len(v) > 2 and v[2].isdigit() else 0
            if pid:
                if pid not in valoraciones:
                    valoraciones[pid] = {"total": 0, "cuenta": 0}
                valoraciones[pid]["total"] += estrellas
                valoraciones[pid]["cuenta"] += 1
    except Exception:
        pass

    productos = []
    for fila in datos:
        if len(fila) >= 2 and fila[1].strip():
            email_asoc = fila[1].strip()
            if email_asoc not in verificados:
                continue
            prod_nombre = fila[2].strip() if len(fila) > 2 else ""
            prod_desc = fila[3].strip() if len(fila) > 3 else ""
            prod_tipo = fila[7].strip().lower() if len(fila) > 7 and fila[7].strip() else ""
            prod_tipo_precio = fila[8].strip().lower() if len(fila) > 8 and fila[8].strip() else ""

            if q and q.strip():
                search = q.strip().lower()
                if search not in prod_nombre.lower() and search not in prod_desc.lower():
                    continue
            if tipo and tipo.strip():
                if prod_tipo != tipo.strip().lower():
                    continue
            if tipo_precio and tipo_precio.strip():
                if prod_tipo_precio != tipo_precio.strip().lower():
                    continue

            prod_id = fila[0].strip() if fila[0].strip() else ""
            val = valoraciones.get(prod_id, {"total": 0, "cuenta": 0})
            promedio = round(val["total"] / val["cuenta"], 1) if val["cuenta"] > 0 else 0
            asoc_info = whatsapp_info.get(email_asoc, {"show_whatsapp": "", "telefono": ""})

            productos.append({
                "id": prod_id,
                "nombre": prod_nombre,
                "descripcion": prod_desc,
                "precio": fila[4].strip() if len(fila) > 4 else "",
                "imagen": fila[5].strip() if len(fila) > 5 and fila[5].strip() else "https://placehold.co/300x200/5B8C51/white?text=Producto",
                "asociacion": email_asoc,
                "asociacion_nombre": nombres_asoc.get(email_asoc, email_asoc),
                "logo_url": logos.get(email_asoc, ""),
                "tipo": prod_tipo,
                "tipo_precio": prod_tipo_precio,
                "estrellas": promedio,
                "num_valoraciones": val["cuenta"],
                "show_whatsapp": asoc_info["show_whatsapp"],
                "telefono": asoc_info["telefono"]
            })

    total_productos = len(productos)
    per_page = 6
    total_pages = max(1, (total_productos + per_page - 1) // per_page)
    page = min(page, total_pages)
    start = (page - 1) * per_page
    end = start + per_page
    productos_paginados = productos[start:end]

    return templates.TemplateResponse("catalogo.html", {
        "request": request,
        "productos": productos_paginados,
        "q": q or "",
        "tipo": tipo or "",
        "tipo_precio": tipo_precio or "",
        "page": page,
        "total_pages": total_pages,
        "total_productos": total_productos
    })

# ─── DASHBOARD ──────────────────────────────────────
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    if "usuario" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=303)

    email = request.session["usuario"]
    try:
        sheet_prod = get_products_sheet()
        todos = sheet_prod.get_all_values()
        datos = todos[1:] if len(todos) > 1 else []
        mis_productos = [fila for fila in datos if len(fila) > 1 and fila[1].strip() == email]
    except Exception:
        mis_productos = []

    total = len(mis_productos)
    productos_por_tipo = {"producto": 0, "servicio": 0}
    for p in mis_productos:
        t = p[7].strip().lower() if len(p) > 7 else ""
        if t in productos_por_tipo:
            productos_por_tipo[t] += 1

    ultimos = []
    for p in reversed(mis_productos[-5:]):
        ultimos.append({
            "nombre": p[2] if len(p) > 2 else "",
            "precio": p[4] if len(p) > 4 else "",
            "imagen": p[5] if len(p) > 5 else "",
            "tipo": p[7] if len(p) > 7 else "",
            "tipo_precio": p[8] if len(p) > 8 else ""
        })

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "usuario": request.session.get("nombre_asociacion", email),
        "total_productos": total,
        "ultimos_productos": ultimos,
        "productos_por_tipo": productos_por_tipo
    })

# ─── PANEL ─────────────────────────────────────────
@app.get("/panel", response_class=HTMLResponse)
def panel(request: Request):
    if "usuario" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=303)

    email = request.session["usuario"]
    try:
        sheet_prod = get_products_sheet()
        todos = sheet_prod.get_all_values()
        datos = todos[1:] if len(todos) > 1 else []
        mis_productos = [fila for fila in datos if len(fila) > 1 and fila[1].strip() == email]
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

# ─── CREAR PRODUCTO ────────────────────────────────
@app.post("/panel/producto")
def crear_producto(
    request: Request,
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
    producto_id = str(uuid.uuid4())
    imagen_url = ""

    if imagen and imagen.filename:
        try:
            result = cloudinary.uploader.upload(
                imagen.file,
                folder="productos",
                filename=imagen.filename,
                use_filename=True,
                unique_filename=True,
                access_mode="public"
            )
            imagen_url = result.get("secure_url", "")
        except Exception:
            pass

    try:
        sheet_prod = get_products_sheet()
        sheet_prod.append_row([producto_id, email, nombre, descripcion or "", precio, imagen_url, str(datetime.datetime.now()), tipo, tipo_precio])
    except Exception:
        pass

    return RedirectResponse(url="/panel", status_code=303)

# ─── EDITAR PRODUCTO (GET) ─────────────────────────
@app.get("/panel/producto/editar/{producto_id}", response_class=HTMLResponse)
def editar_producto_form(request: Request, producto_id: str):
    if "usuario" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=303)

    email = request.session["usuario"]
    try:
        sheet_prod = get_products_sheet()
        todos = sheet_prod.get_all_values()[1:]
        for fila in todos:
            if len(fila) > 0 and fila[0] == producto_id and len(fila) > 1 and fila[1] == email:
                producto = {
                    "id": fila[0],
                    "nombre": fila[2] if len(fila) > 2 else "",
                    "descripcion": fila[3] if len(fila) > 3 else "",
                    "precio": fila[4] if len(fila) > 4 else "",
                    "imagen_url": fila[5] if len(fila) > 5 else "",
                    "tipo": fila[7] if len(fila) > 7 else "producto",
                    "tipo_precio": fila[8] if len(fila) > 8 else "fijo"
                }
                return templates.TemplateResponse("editar_producto.html", {"request": request, "producto": producto})
        return RedirectResponse(url="/panel", status_code=303)
    except Exception:
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
        for i, fila in enumerate(todos):
            if i == 0:
                continue
            if len(fila) > 0 and fila[0] == producto_id and len(fila) > 1 and fila[1] == email:
                antigua_imagen = fila[5] if len(fila) > 5 and fila[5].strip() else ""
                nueva_imagen = antigua_imagen

                if imagen and imagen.filename:
                    if antigua_imagen:
                        delete_cloudinary_asset(antigua_imagen, resource_type="image")
                    try:
                        result = cloudinary.uploader.upload(
                            imagen.file,
                            folder="productos",
                            filename=imagen.filename,
                            use_filename=True,
                            unique_filename=True,
                            access_mode="public"
                        )
                        nueva_imagen = result.get("secure_url", "")
                    except Exception:
                        pass

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
    except Exception:
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
            if len(fila) > 0 and fila[0] == producto_id and len(fila) > 1 and fila[1] == email:
                imagen_url = fila[5] if len(fila) > 5 and fila[5].strip() else ""
                if imagen_url:
                    delete_cloudinary_asset(imagen_url, resource_type="image")
                sheet_prod.delete_rows(i + 1)
                break
    except Exception as e:
        logging.exception("Error al eliminar producto")
    return RedirectResponse(url="/panel", status_code=303)

# ─── EDITAR PERFIL (GET) ───────────────────────────
@app.get("/panel/editar-perfil", response_class=HTMLResponse)
def editar_perfil_form(request: Request):
    if "usuario" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=303)

    email = request.session["usuario"]
    try:
        sheet_usr = get_sheet()
        usuarios = sheet_usr.get_all_values()[1:]
        for u in usuarios:
            if u[0] == email:
                perfil = {
                    "email": u[0],
                    "nombre": u[3] if len(u) > 3 else "",
                    "descripcion": u[4] if len(u) > 4 else "",
                    "direccion": u[5] if len(u) > 5 else "",
                    "telefono": u[6] if len(u) > 6 else "",
                    "logo_url": u[7].strip() if len(u) > 7 and u[7].strip() else "",
                    "show_whatsapp": u[8].strip() if len(u) > 8 else "",
                    "camara_comercio_url": u[9].strip() if len(u) > 9 and u[9].strip() else "",
                    "rut_url": u[10].strip() if len(u) > 10 and u[10].strip() else ""
                }
                return templates.TemplateResponse("editar_perfil.html", {"request": request, "perfil": perfil})
    except Exception:
        pass
    return RedirectResponse(url="/panel", status_code=303)

# ─── ACTUALIZAR PERFIL ─────────────────────────────
@app.post("/panel/editar-perfil")
def actualizar_perfil(
    request: Request,
    nombre_asociacion: str = Form(...),
    descripcion: str = Form(None),
    direccion: str = Form(None),
    telefono: str = Form(None),
    show_whatsapp: str = Form(None),
    logo: UploadFile = File(None),
    camara_comercio: UploadFile = File(None),
    rut: UploadFile = File(None)
):
    if "usuario" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=303)

    email = request.session["usuario"]
    logo_url = request.session.get("logo_url", "")
    try:
        sheet_usr = get_sheet()
        usuarios = sheet_usr.get_all_values()
        for i, u in enumerate(usuarios):
            if i == 0:
                continue
            if u[0] == email:
                # ── Logo ──
                if logo and logo.filename:
                    if u[7].strip():
                        delete_cloudinary_asset(u[7].strip(), resource_type="image")
                    try:
                        result = cloudinary.uploader.upload(
                            logo.file,
                            folder="logos",
                            filename=logo.filename,
                            use_filename=True,
                            unique_filename=True,
                            access_mode="public"
                        )
                        logo_url = result.get("secure_url", "")
                    except Exception:
                        pass

                # ── Cámara de Comercio ──
                camara_url = u[9] if len(u) > 9 else ""
                if camara_comercio and camara_comercio.filename:
                    if camara_url:
                        delete_cloudinary_asset(camara_url, resource_type="raw")
                    try:
                        result = cloudinary.uploader.upload(
                            camara_comercio.file,
                            folder="documentos",
                            resource_type="raw",
                            filename=camara_comercio.filename,
                            use_filename=True,
                            unique_filename=True,
                            access_mode="public"
                        )
                        camara_url = result.get("secure_url", "")
                    except Exception:
                        pass

                # ── RUT ──
                rut_url = u[10] if len(u) > 10 else ""
                if rut and rut.filename:
                    if rut_url:
                        delete_cloudinary_asset(rut_url, resource_type="raw")
                    try:
                        result = cloudinary.uploader.upload(
                            rut.file,
                            folder="documentos",
                            resource_type="raw",
                            filename=rut.filename,
                            use_filename=True,
                            unique_filename=True,
                            access_mode="public"
                        )
                        rut_url = result.get("secure_url", "")
                    except Exception:
                        pass

                # Actualizar fila completa (hasta columna L)
                sheet_usr.update(f'A{i+1}:L{i+1}', [[
                    email,
                    u[1],
                    u[2],
                    nombre_asociacion,
                    descripcion or "",
                    direccion or "",
                    telefono or "",
                    logo_url,
                    "1" if show_whatsapp == "1" else "",
                    camara_url,
                    rut_url,
                    u[11] if len(u) > 11 else ""
                ]])

                request.session["nombre_asociacion"] = nombre_asociacion
                request.session["logo_url"] = logo_url
                request.session["show_whatsapp"] = "1" if show_whatsapp == "1" else ""
                request.session["telefono"] = telefono or ""
                break
    except Exception as e:
        logging.exception("Error al actualizar perfil")

    return RedirectResponse(url="/panel", status_code=303)

# ─── PERFIL PÚBLICO DE ASOCIACIÓN ─────────────────
@app.get("/asociacion/{email}", response_class=HTMLResponse)
def perfil_asociacion(request: Request, email: str):
    asociacion = None
    try:
        sheet_usr = get_sheet()
        usuarios = sheet_usr.get_all_values()[1:]
        for u in usuarios:
            if u[0] == email:
                if len(u) <= 11 or u[11].strip() != "1":
                    return RedirectResponse(url="/catalogo", status_code=303)
                asociacion = {
                    "email": u[0],
                    "nombre": u[3] if len(u) > 3 else u[0],
                    "descripcion": u[4] if len(u) > 4 else "",
                    "direccion": u[5] if len(u) > 5 else "",
                    "telefono": u[6] if len(u) > 6 else "",
                    "logo_url": u[7].strip() if len(u) > 7 and u[7].strip() else "",
                    "show_whatsapp": u[8].strip() if len(u) > 8 else ""
                }
                break
    except Exception:
        pass

    if not asociacion:
        return RedirectResponse(url="/catalogo", status_code=303)

    productos = []
    try:
        sheet_prod = get_products_sheet()
        todos = sheet_prod.get_all_values()[1:]
        for fila in todos:
            if len(fila) > 1 and fila[1] == email:
                productos.append({
                    "nombre": fila[2] if len(fila) > 2 else "",
                    "descripcion": fila[3] if len(fila) > 3 else "",
                    "precio": fila[4] if len(fila) > 4 else "",
                    "imagen": fila[5].strip() if len(fila) > 5 and fila[5].strip() else "https://placehold.co/300x200/5B8C51/white?text=Producto",
                    "tipo": fila[7] if len(fila) > 7 else "",
                    "tipo_precio": fila[8] if len(fila) > 8 else ""
                })
    except Exception:
        pass

    return templates.TemplateResponse("perfil.html", {
        "request": request,
        "asociacion": asociacion,
        "productos": productos
    })

# ─── VALORAR PRODUCTO ──────────────────────────────
@app.post("/valorar/{producto_id}")
def valorar_producto(
    request: Request,
    producto_id: str,
    estrellas: int = Form(...),
    comentario: str = Form(None)
):
    if "usuario" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=303)

    if estrellas < 1 or estrellas > 5:
        return RedirectResponse(url="/catalogo", status_code=303)

    email = request.session["usuario"]
    try:
        sheet_val = get_valoraciones_sheet()
        sheet_val.append_row([
            str(uuid.uuid4()),
            producto_id,
            estrellas,
            comentario or "",
            str(datetime.datetime.now()),
            email
        ])
    except Exception:
        pass

    return RedirectResponse(url="/catalogo", status_code=303)