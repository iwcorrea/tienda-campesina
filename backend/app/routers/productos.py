from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import obtener_usuario_actual
from .. import models
from ..dependencies import templates
from ..services.google_drive import crear_carpeta_si_no_existe, subir_archivo, eliminar_archivo, obtener_url_directa
import os

router = APIRouter(prefix="/productos", tags=["productos"])
ROOT_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

@router.get("/", response_class=HTMLResponse)
def lista_productos(request: Request, db: Session = Depends(get_db), usuario=Depends(obtener_usuario_actual)):
    productos = db.query(models.Producto).filter(models.Producto.asociacion_id == usuario.id).all()
    for p in productos:
        p.imagen_url = obtener_url_directa(p.imagen_file_id) if p.imagen_file_id else None
    template = templates.env.get_template("lista_productos.html")
    return HTMLResponse(content=template.render({"request": request, "productos": productos}))

@router.get("/crear", response_class=HTMLResponse)
def crear_producto_form(request: Request, usuario=Depends(obtener_usuario_actual)):
    template = templates.env.get_template("crear_producto.html")
    return HTMLResponse(content=template.render({"request": request}))

@router.post("/crear")
async def crear_producto(
    request: Request,
    nombre: str = Form(...),
    descripcion: str = Form(None),
    precio: int = Form(None),
    imagen: UploadFile = File(None),
    db: Session = Depends(get_db),
    usuario=Depends(obtener_usuario_actual)
):
    carpeta_usuario = await crear_carpeta_si_no_existe(f"asociacion_{usuario.id}", parent_id=ROOT_FOLDER_ID)
    imagen_id = None
    if imagen and imagen.filename:
        imagen_id = await subir_archivo(imagen, carpeta_usuario)
    nuevo = models.Producto(
        asociacion_id=usuario.id,
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        imagen_file_id=imagen_id
    )
    db.add(nuevo)
    db.commit()
    return RedirectResponse(url="/productos", status_code=303)

@router.get("/editar/{id}", response_class=HTMLResponse)
def editar_producto_form(request: Request, id: int, db: Session = Depends(get_db), usuario=Depends(obtener_usuario_actual)):
    producto = db.query(models.Producto).filter(models.Producto.id == id, models.Producto.asociacion_id == usuario.id).first()
    if not producto:
        raise HTTPException(404, "Producto no encontrado")
    template = templates.env.get_template("editar_producto.html")
    return HTMLResponse(content=template.render({"request": request, "producto": producto}))

@router.post("/editar/{id}")
async def editar_producto(
    id: int,
    nombre: str = Form(...),
    descripcion: str = Form(None),
    precio: int = Form(None),
    disponible: int = Form(1),
    imagen: UploadFile = File(None),
    db: Session = Depends(get_db),
    usuario=Depends(obtener_usuario_actual)
):
    producto = db.query(models.Producto).filter(models.Producto.id == id, models.Producto.asociacion_id == usuario.id).first()
    if not producto:
        raise HTTPException(404, "Producto no encontrado")
    if imagen and imagen.filename:
        if producto.imagen_file_id:
            eliminar_archivo(producto.imagen_file_id)
        carpeta = await crear_carpeta_si_no_existe(f"asociacion_{usuario.id}", parent_id=ROOT_FOLDER_ID)
        producto.imagen_file_id = await subir_archivo(imagen, carpeta)
    producto.nombre = nombre
    producto.descripcion = descripcion
    producto.precio = precio
    producto.disponible = disponible
    db.commit()
    return RedirectResponse(url="/productos", status_code=303)

@router.post("/eliminar/{id}")
def eliminar_producto(id: int, db: Session = Depends(get_db), usuario=Depends(obtener_usuario_actual)):
    producto = db.query(models.Producto).filter(models.Producto.id == id, models.Producto.asociacion_id == usuario.id).first()
    if producto:
        if producto.imagen_file_id:
            eliminar_archivo(producto.imagen_file_id)
        db.delete(producto)
        db.commit()
    return RedirectResponse(url="/productos", status_code=303)