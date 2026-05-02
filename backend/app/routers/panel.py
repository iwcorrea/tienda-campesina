import logging
import os
import uuid
from fastapi import APIRouter, Request, Form, File, UploadFile, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Asociacion, Producto
import cloudinary.uploader

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger("panel")

# ─── PANEL ─────────────────────────────────────────
@router.get("/panel", response_class=HTMLResponse)
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

# ─── CREAR PRODUCTO ────────────────────────────────
@router.post("/panel/producto")
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

# ─── EDITAR PRODUCTO (GET) ─────────────────────────
@router.get("/panel/producto/editar/{producto_id}", response_class=HTMLResponse)
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

# ─── ACTUALIZAR PRODUCTO ───────────────────────────
@router.post("/panel/producto/actualizar/{producto_id}")
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
            from app.main import delete_cloudinary_asset
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

# ─── ELIMINAR PRODUCTO ─────────────────────────────
@router.post("/panel/producto/eliminar/{producto_id}")
def eliminar_producto(request: Request, producto_id: str, db: Session = Depends(get_db)):
    if "usuario" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    p = db.query(Producto).filter(Producto.id == producto_id, Producto.asociacion_email == email).first()
    if p:
        if p.imagen_url:
            from app.main import delete_cloudinary_asset
            delete_cloudinary_asset(p.imagen_url, resource_type="image")
        db.delete(p)
        db.commit()
    return RedirectResponse(url="/panel", status_code=303)

    # ─── TRANSPORTADORES ─────────────────────────────
@router.get("/panel/transportadores", response_class=HTMLResponse)
def panel_transportadores(request: Request, db: Session = Depends(get_db)):
    if request.session.get("tipo_usuario") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    transportadores = db.query(Transportador).filter(
        Transportador.asociacion_email == email
    ).order_by(Transportador.nombre).all()
    return templates.TemplateResponse("panel_transportadores.html", {
        "request": request,
        "transportadores": transportadores
    })

@router.post("/panel/transportadores/crear")
def crear_transportador(
    request: Request,
    nombre: str = Form(...),
    medio: str = Form("camioneta"),
    tarifa_base: int = Form(5000),
    costo_km: int = Form(1500),
    telefono: str = Form(""),
    db: Session = Depends(get_db)
):
    if request.session.get("tipo_usuario") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    nuevo = Transportador(
        asociacion_email=email,
        nombre=nombre,
        medio=medio,
        tarifa_base=tarifa_base,
        costo_km=costo_km,
        telefono=telefono
    )
    db.add(nuevo)
    db.commit()
    return RedirectResponse(url="/panel/transportadores", status_code=303)

@router.post("/panel/transportadores/eliminar/{transportador_id}")
def eliminar_transportador(
    request: Request,
    transportador_id: str,
    db: Session = Depends(get_db)
):
    if request.session.get("tipo_usuario") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    t = db.query(Transportador).filter(
        Transportador.id == transportador_id,
        Transportador.asociacion_email == email
    ).first()
    if t:
        db.delete(t)
        db.commit()
    return RedirectResponse(url="/panel/transportadores", status_code=303)

# ─── API PARA CALCULAR ENVÍO (usada por el modal) ─
@router.get("/api/calcular-envio/{asociacion_email}")
def calcular_envio(
    asociacion_email: str,
    distancia: float = Query(0),
    peso: float = Query(0),
    db: Session = Depends(get_db)
):
    transportadores = db.query(Transportador).filter(
        Transportador.asociacion_email == asociacion_email,
        Transportador.activo == "1"
    ).all()
    resultados = []
    for t in transportadores:
        costo = t.tarifa_base + (t.costo_km * distancia) + (peso * 200)  # $200 extra por kg
        resultados.append({
            "nombre": t.nombre,
            "medio": t.medio,
            "telefono": t.telefono,
            "costo_estimado": round(costo)
        })
    return resultados  # FastAPI convertirá a JSON automáticamente