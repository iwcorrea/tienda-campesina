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
    for producto in productos:
        if producto.imagen_file_id:
            producto.imagen_url = obtener_url_directa(producto.imagen_file_id)
        else:
            producto.imagen_url = None
    return templates.TemplateResponse("lista_productos.html", {"request": request, "productos": productos})

@router.get("/crear", response_class=HTMLResponse)
def crear_producto_form(request: Request, usuario=Depends(obtener_usuario_actual)):
    return templates.TemplateResponse("crear_producto.html", {"request": request})

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
    nuevo_producto = models.Producto(
        asociacion_id=usuario.id,
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        imagen_file_id=imagen_id
    )
    db.add(nuevo_producto)
    db.commit()
    return RedirectResponse(url="/productos", status_code=303)

@router.get("/editar/{producto_id}", response_class=HTMLResponse)
def editar_producto_form(request: Request, producto_id: int, db: Session = Depends(get_db), usuario=Depends(obtener_usuario_actual)):
    producto = db.query(models.Producto).filter(models.Producto.id == producto_id, models.Producto.asociacion_id == usuario.id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return templates.TemplateResponse("editar_producto.html", {"request": request, "producto": producto})

@router.post("/editar/{producto_id}")
async def editar_producto(
    request: Request,
    producto_id: int,
    nombre: str = Form(...),
    descripcion: str = Form(None),
    precio: int = Form(None),
    disponible: int = Form(1),
    imagen: UploadFile = File(None),
    db: Session = Depends(get_db),
    usuario=Depends(obtener_usuario_actual)
):
    producto = db.query(models.Producto).filter(models.Producto.id == producto_id, models.Producto.asociacion_id == usuario.id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    producto.nombre = nombre
    producto.descripcion = descripcion
    producto.precio = precio
    producto.disponible = disponible
    if imagen and imagen.filename:
        if producto.imagen_file_id:
            eliminar_archivo(producto.imagen_file_id)
        carpeta_usuario = await crear_carpeta_si_no_existe(f"asociacion_{usuario.id}", parent_id=ROOT_FOLDER_ID)
        imagen_id = await subir_archivo(imagen, carpeta_usuario)
        producto.imagen_file_id = imagen_id
    db.commit()
    return RedirectResponse(url="/productos", status_code=303)

@router.post("/eliminar/{producto_id}")
def eliminar_producto(
    producto_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(obtener_usuario_actual)
):
    producto = db.query(models.Producto).filter(models.Producto.id == producto_id, models.Producto.asociacion_id == usuario.id).first()
    if producto:
        if producto.imagen_file_id:
            eliminar_archivo(producto.imagen_file_id)
        db.delete(producto)
        db.commit()
    return RedirectResponse(url="/productos", status_code=303)