# (Copia todo el contenido que viene a continuación)
import logging
import os
import uuid
from fastapi import FastAPI, Request, Form, File, UploadFile, Query, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.auth import router as auth_router
from app.database import engine, get_db, Base
from app.models import Asociacion, Producto, Valoracion
import cloudinary
import cloudinary.uploader
import cloudinary.api
import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

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

# Crear tablas al iniciar si no existen
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

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
        if resource_type in ("image", "video"):
            public_id = public_id_with_ext.rsplit(".", 1)[0]
        else:
            public_id = public_id_with_ext
        cloudinary.uploader.destroy(public_id, resource_type=resource_type)
    except Exception as e:
        logging.exception("Error al eliminar recurso")

# ─── HOME ───
@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
def inicio(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ─── MENÚ ───
@app.get("/menu", response_class=HTMLResponse)
def menu(request: Request):
    return templates.TemplateResponse("menu.html", {"request": request})

# ─── CATÁLOGO ───
@app.get("/catalogo", response_class=HTMLResponse)
def catalogo(
    request: Request,
    q: str = Query(default=None),
    tipo: str = Query(default=None),
    tipo_precio: str = Query(default=None),
    page: int = Query(default=1, ge=1),
    db: Session = Depends(get_db)
):
    query = db.query(Producto).join(Asociacion).filter(Asociacion.verificado == "1")

    if q:
        search = f"%{q}%"
        query = query.filter(
            (Producto.nombre.ilike(search)) | (Producto.descripcion.ilike(search))
        )
    if tipo:
        query = query.filter(Producto.tipo == tipo)
    if tipo_precio:
        query = query.filter(Producto.tipo_precio == tipo_precio)

    total_productos = query.count()
    per_page = 6
    total_pages = max(1, (total_productos + per_page - 1) // per_page)
    page = min(page, total_pages)
    productos_db = query.order_by(Producto.fecha_creacion.desc()).offset((page - 1) * per_page).limit(per_page).all()

    productos = []
    for p in productos_db:
        # Obtener valoraciones de este producto
        estrellas_data = db.query(
            func.avg(Valoracion.estrellas), func.count(Valoracion.id)
        ).filter(Valoracion.producto_id == p.id).first()
        promedio = round(float(estrellas_data[0]), 1) if estrellas_data[0] else 0
        num = estrellas_data[1]

        asociacion = p.asociacion
        productos.append({
            "id": p.id,
            "nombre": p.nombre,
            "descripcion": p.descripcion,
            "precio": p.precio,
            "imagen": p.imagen_url or "https://placehold.co/300x200/5B8C51/white?text=Producto",
            "asociacion": asociacion.email,
            "asociacion_nombre": asociacion.nombre,
            "logo_url": asociacion.logo_url or "",
            "tipo": p.tipo,
            "tipo_precio": p.tipo_precio,
            "estrellas": promedio,
            "num_valoraciones": num,
            "show_whatsapp": asociacion.show_whatsapp,
            "telefono": asociacion.telefono
        })

    return templates.TemplateResponse("catalogo.html", {
        "request": request,
        "productos": productos,
        "q": q or "",
        "tipo": tipo or "",
        "tipo_precio": tipo_precio or "",
        "page": page,
        "total_pages": total_pages,
        "total_productos": total_productos
    })

# ─── DASHBOARD ───
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    if "usuario" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    asociacion = db.query(Asociacion).filter(Asociacion.email == email).first()
    if not asociacion:
        return RedirectResponse(url="/auth/login", status_code=303)

    mis_productos = asociacion.productos
    total = len(mis_productos)
    productos_por_tipo = {"producto": 0, "servicio": 0}
    for p in mis_productos:
        productos_por_tipo[p.tipo] = productos_por_tipo.get(p.tipo, 0) + 1

    ultimos = []
    for p in reversed(mis_productos[-5:]):
        ultimos.append({
            "nombre": p.nombre,
            "precio": p.precio,
            "imagen": p.imagen_url,
            "tipo": p.tipo,
            "tipo_precio": p.tipo_precio
        })

    # Valoraciones de los productos
    total_valoraciones = 0
    suma_estrellas = 0
    distribucion_estrellas = [0, 0, 0, 0, 0]
    ultimas_valoraciones = []
    try:
        all_vals = db.query(Valoracion).filter(Valoracion.producto_id.in_([p.id for p in mis_productos])).all()
        total_valoraciones = len(all_vals)
        for v in all_vals:
            est = v.estrellas
            suma_estrellas += est
            if 1 <= est <= 5:
                distribucion_estrellas[est - 1] += 1
        all_vals.sort(key=lambda x: x.fecha, reverse=True)
        for v in all_vals[:5]:
            prod = db.query(Producto).filter(Producto.id == v.producto_id).first()
            ultimas_valoraciones.append({
                "producto_nombre": prod.nombre if prod else "Producto",
                "estrellas": v.estrellas,
                "comentario": v.comentario or ""
            })
    except Exception:
        pass

    promedio_estrellas = round(suma_estrellas / total_valoraciones, 1) if total_valoraciones > 0 else 0

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "usuario": asociacion.nombre,
        "total_productos": total,
        "ultimos_productos": ultimos,
        "productos_por_tipo": productos_por_tipo,
        "total_valoraciones": total_valoraciones,
        "promedio_estrellas": promedio_estrellas,
        "distribucion_estrellas": distribucion_estrellas,
        "ultimas_valoraciones": ultimas_valoraciones
    })

# ─── PANEL ───
@app.get("/panel", response_class=HTMLResponse)
def panel(request: Request, db: Session = Depends(get_db)):
    if "usuario" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    asociacion = db.query(Asociacion).filter(Asociacion.email == email).first()
    if not asociacion:
        return RedirectResponse(url="/auth/login", status_code=303)

    productos_obj = []
    for p in asociacion.productos:
        productos_obj.append({
            "id": p.id,
            "nombre": p.nombre,
            "descripcion": p.descripcion,
            "precio": p.precio,
            "imagen": p.imagen_url,
            "tipo": p.tipo,
            "tipo_precio": p.tipo_precio
        })

    return templates.TemplateResponse("panel.html", {
        "request": request,
        "usuario": asociacion.nombre,
        "productos": productos_obj
    })

# ─── CREAR PRODUCTO ───
@app.post("/panel/producto")
def crear_producto(
    request: Request,
    nombre: str = Form(...),
    descripcion: str = Form(None),
    precio: int = Form(...),
    tipo: str = Form("producto"),
    tipo_precio: str = Form("fijo"),
    imagen: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    if "usuario" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
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

    nuevo = Producto(
        id=str(uuid.uuid4()),
        asociacion_email=email,
        nombre=nombre,
        descripcion=descripcion or "",
        precio=precio,
        imagen_url=imagen_url,
        tipo=tipo,
        tipo_precio=tipo_precio
    )
    db.add(nuevo)
    db.commit()
    return RedirectResponse(url="/panel", status_code=303)

# ─── EDITAR PRODUCTO (GET) ───
@app.get("/panel/producto/editar/{producto_id}", response_class=HTMLResponse)
def editar_producto_form(request: Request, producto_id: str, db: Session = Depends(get_db)):
    if "usuario" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    p = db.query(Producto).filter(Producto.id == producto_id, Producto.asociacion_email == email).first()
    if not p:
        return RedirectResponse(url="/panel", status_code=303)
    producto = {
        "id": p.id,
        "nombre": p.nombre,
        "descripcion": p.descripcion,
        "precio": p.precio,
        "imagen_url": p.imagen_url,
        "tipo": p.tipo,
        "tipo_precio": p.tipo_precio
    }
    return templates.TemplateResponse("editar_producto.html", {"request": request, "producto": producto})

# ─── ACTUALIZAR PRODUCTO ───
@app.post("/panel/producto/actualizar/{producto_id}")
def actualizar_producto(
    request: Request,
    producto_id: str,
    nombre: str = Form(...),
    descripcion: str = Form(None),
    precio: int = Form(...),
    tipo: str = Form("producto"),
    tipo_precio: str = Form("fijo"),
    imagen: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    if "usuario" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    p = db.query(Producto).filter(Producto.id == producto_id, Producto.asociacion_email == email).first()
    if not p:
        return RedirectResponse(url="/panel", status_code=303)

    if imagen and imagen.filename:
        if p.imagen_url:
            delete_cloudinary_asset(p.imagen_url, resource_type="image")
        try:
            result = cloudinary.uploader.upload(
                imagen.file,
                folder="productos",
                filename=imagen.filename,
                use_filename=True,
                unique_filename=True,
                access_mode="public"
            )
            p.imagen_url = result.get("secure_url", "")
        except Exception:
            pass

    p.nombre = nombre
    p.descripcion = descripcion or ""
    p.precio = precio
    p.tipo = tipo
    p.tipo_precio = tipo_precio
    db.commit()
    return RedirectResponse(url="/panel", status_code=303)

# ─── ELIMINAR PRODUCTO ───
@app.post("/panel/producto/eliminar/{producto_id}")
def eliminar_producto(request: Request, producto_id: str, db: Session = Depends(get_db)):
    if "usuario" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    p = db.query(Producto).filter(Producto.id == producto_id, Producto.asociacion_email == email).first()
    if p:
        if p.imagen_url:
            delete_cloudinary_asset(p.imagen_url, resource_type="image")
        db.delete(p)
        db.commit()
    return RedirectResponse(url="/panel", status_code=303)

# ─── EDITAR PERFIL (GET) ───
@app.get("/panel/editar-perfil", response_class=HTMLResponse)
def editar_perfil_form(request: Request, db: Session = Depends(get_db)):
    if "usuario" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    a = db.query(Asociacion).filter(Asociacion.email == email).first()
    if not a:
        return RedirectResponse(url="/panel", status_code=303)
    perfil = {
        "email": a.email,
        "nombre": a.nombre,
        "descripcion": a.descripcion,
        "direccion": a.direccion,
        "telefono": a.telefono,
        "logo_url": a.logo_url,
        "show_whatsapp": a.show_whatsapp,
        "camara_comercio_url": a.camara_url,
        "rut_url": a.rut_url
    }
    return templates.TemplateResponse("editar_perfil.html", {"request": request, "perfil": perfil})

# ─── ACTUALIZAR PERFIL ───
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
    rut: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    if "usuario" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    a = db.query(Asociacion).filter(Asociacion.email == email).first()
    if not a:
        return RedirectResponse(url="/panel", status_code=303)

    if logo and logo.filename:
        if a.logo_url:
            delete_cloudinary_asset(a.logo_url, resource_type="image")
        try:
            result = cloudinary.uploader.upload(
                logo.file,
                folder="logos",
                filename=logo.filename,
                use_filename=True,
                unique_filename=True,
                access_mode="public"
            )
            a.logo_url = result.get("secure_url", "")
        except Exception:
            pass

    if camara_comercio and camara_comercio.filename:
        if a.camara_url:
            delete_cloudinary_asset(a.camara_url, resource_type="raw")
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
            a.camara_url = result.get("secure_url", "")
        except Exception:
            pass

    if rut and rut.filename:
        if a.rut_url:
            delete_cloudinary_asset(a.rut_url, resource_type="raw")
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
            a.rut_url = result.get("secure_url", "")
        except Exception:
            pass

    a.nombre = nombre_asociacion
    a.descripcion = descripcion or ""
    a.direccion = direccion or ""
    a.telefono = telefono or ""
    a.show_whatsapp = "1" if show_whatsapp == "1" else ""
    db.commit()

    request.session["nombre_asociacion"] = a.nombre
    request.session["logo_url"] = a.logo_url
    request.session["show_whatsapp"] = a.show_whatsapp
    request.session["telefono"] = a.telefono
    return RedirectResponse(url="/panel", status_code=303)

# ─── PERFIL PÚBLICO ───
@app.get("/asociacion/{email}", response_class=HTMLResponse)
def perfil_asociacion(request: Request, email: str, db: Session = Depends(get_db)):
    a = db.query(Asociacion).filter(Asociacion.email == email, Asociacion.verificado == "1").first()
    if not a:
        return RedirectResponse(url="/catalogo", status_code=303)
    productos = []
    for p in a.productos:
        productos.append({
            "nombre": p.nombre,
            "descripcion": p.descripcion,
            "precio": p.precio,
            "imagen": p.imagen_url or "https://placehold.co/300x200/5B8C51/white?text=Producto",
            "tipo": p.tipo,
            "tipo_precio": p.tipo_precio
        })
    asociacion = {
        "email": a.email,
        "nombre": a.nombre,
        "descripcion": a.descripcion,
        "direccion": a.direccion,
        "telefono": a.telefono,
        "logo_url": a.logo_url,
        "show_whatsapp": a.show_whatsapp
    }
    return templates.TemplateResponse("perfil.html", {"request": request, "asociacion": asociacion, "productos": productos})

# ─── VALORAR PRODUCTO ───
@app.post("/valorar/{producto_id}")
def valorar_producto(
    request: Request,
    producto_id: str,
    estrellas: int = Form(...),
    comentario: str = Form(None),
    db: Session = Depends(get_db)
):
    if "usuario" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=303)
    if estrellas < 1 or estrellas > 5:
        return RedirectResponse(url="/catalogo", status_code=303)
    email = request.session["usuario"]
    val = Valoracion(
        id=str(uuid.uuid4()),
        producto_id=producto_id,
        estrellas=estrellas,
        comentario=comentario or "",
        email_usuario=email
    )
    db.add(val)
    db.commit()
    return RedirectResponse(url="/catalogo", status_code=303)

# ════════════════════ ADMIN ════════════════════
@app.get("/admin", response_class=HTMLResponse)
def admin_panel(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("es_admin"):
        return RedirectResponse(url="/auth/login", status_code=303)
    asociaciones = db.query(Asociacion).all()
    data = []
    for a in asociaciones:
        data.append({
            "email": a.email,
            "nombre": a.nombre,
            "camara_url": a.camara_url,
            "rut_url": a.rut_url,
            "verificado": a.verificado
        })
    return templates.TemplateResponse("admin.html", {"request": request, "asociaciones": data})

@app.post("/admin/toggle-estado/{email}")
def admin_toggle_estado(request: Request, email: str, db: Session = Depends(get_db)):
    if not request.session.get("es_admin"):
        return RedirectResponse(url="/auth/login", status_code=303)
    a = db.query(Asociacion).filter(Asociacion.email == email).first()
    if a:
        a.verificado = "" if a.verificado == "1" else "1"
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@app.get("/admin/archivos", response_class=HTMLResponse)
def admin_archivos(request: Request, resource_type: str = "image", next_cursor: str = None):
    if not request.session.get("es_admin"):
        return RedirectResponse(url="/auth/login", status_code=303)
    recursos = []
    cursor = None
    try:
        result = cloudinary.api.resources(
            type="upload",
            resource_type=resource_type,
            max_results=50,
            next_cursor=next_cursor
        )
        recursos = result.get("resources", [])
        cursor = result.get("next_cursor", None)
    except Exception as e:
        logging.exception("Error listando archivos")
    return templates.TemplateResponse("admin_archivos.html", {
        "request": request,
        "recursos": recursos,
        "resource_type": resource_type,
        "next_cursor": cursor
    })

@app.post("/admin/archivos/eliminar")
def admin_eliminar_archivo(
    request: Request,
    public_id: str = Form(...),
    resource_type: str = Form(...)
):
    if not request.session.get("es_admin"):
        return RedirectResponse(url="/auth/login", status_code=303)
    cloudinary.uploader.destroy(public_id, resource_type=resource_type)
    return RedirectResponse(url=f"/admin/archivos?resource_type={resource_type}", status_code=303)

@app.get("/admin/asociacion/{email}/editar", response_class=HTMLResponse)
def admin_editar_asociacion_form(request: Request, email: str, db: Session = Depends(get_db)):
    if not request.session.get("es_admin"):
        return RedirectResponse(url="/auth/login", status_code=303)
    a = db.query(Asociacion).filter(Asociacion.email == email).first()
    if not a:
        return RedirectResponse(url="/admin", status_code=303)
    perfil = {
        "email": a.email,
        "nombre": a.nombre,
        "logo_url": a.logo_url,
        "camara_comercio_url": a.camara_url,
        "rut_url": a.rut_url
    }
    return templates.TemplateResponse("admin_editar_asociacion.html", {"request": request, "perfil": perfil})

@app.post("/admin/asociacion/{email}/actualizar")
def admin_actualizar_asociacion(
    request: Request,
    email: str,
    logo_url: str = Form(""),
    camara_url: str = Form(""),
    rut_url: str = Form(""),
    db: Session = Depends(get_db)
):
    if not request.session.get("es_admin"):
        return RedirectResponse(url="/auth/login", status_code=303)
    a = db.query(Asociacion).filter(Asociacion.email == email).first()
    if a:
        a.logo_url = logo_url.strip()
        a.camara_url = camara_url.strip()
        a.rut_url = rut_url.strip()
        db.commit()
    return RedirectResponse(url=f"/admin/asociacion/{email}/editar", status_code=303)

@app.get("/admin/producto/{producto_id}/editar", response_class=HTMLResponse)
def admin_editar_producto_form(request: Request, producto_id: str, db: Session = Depends(get_db)):
    if not request.session.get("es_admin"):
        return RedirectResponse(url="/auth/login", status_code=303)
    p = db.query(Producto).filter(Producto.id == producto_id).first()
    if not p:
        return RedirectResponse(url="/admin", status_code=303)
    producto = {
        "id": p.id,
        "nombre": p.nombre,
        "precio": p.precio,
        "imagen_url": p.imagen_url
    }
    return templates.TemplateResponse("admin_editar_producto.html", {"request": request, "producto": producto})

@app.post("/admin/producto/{producto_id}/actualizar")
def admin_actualizar_producto(
    request: Request,
    producto_id: str,
    imagen_url: str = Form(""),
    db: Session = Depends(get_db)
):
    if not request.session.get("es_admin"):
        return RedirectResponse(url="/auth/login", status_code=303)
    p = db.query(Producto).filter(Producto.id == producto_id).first()
    if p:
        p.imagen_url = imagen_url.strip()
        db.commit()
    return RedirectResponse(url=f"/admin/producto/{producto_id}/editar", status_code=303)