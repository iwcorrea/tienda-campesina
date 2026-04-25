from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Asociacion, Producto
from ..services.google_drive import crear_carpeta_si_no_existe, eliminar_archivo, subir_archivo

router = APIRouter(tags=["productos"])
templates = Jinja2Templates(directory="backend/app/templates")


def current_user_dependency(request: Request, db: Session = Depends(get_db)) -> Asociacion:
    return get_current_user(request, db)


@router.get("/productos")
def lista_productos(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Asociacion = Depends(current_user_dependency),
):
    productos = db.query(Producto).filter(Producto.asociacion_id == current_user.id).all()
    return templates.TemplateResponse(
        "lista_productos.html",
        {"request": request, "usuario": current_user, "productos": productos},
    )


@router.get("/productos/crear")
def crear_producto_form(
    request: Request,
    current_user: Asociacion = Depends(current_user_dependency),
):
    return templates.TemplateResponse(
        "crear_producto.html",
        {"request": request, "usuario": current_user},
    )


@router.post("/productos/crear")
async def crear_producto_post(
    request: Request,
    nombre: str = Form(...),
    descripcion: str = Form(None),
    precio: int = Form(None),
    disponible: int = Form(1),
    imagen: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: Asociacion = Depends(current_user_dependency),
):
    imagen_file_id = None
    if imagen and imagen.filename:
        carpeta_id = crear_carpeta_si_no_existe(f"asociacion_{current_user.id}")
        imagen_file_id = await subir_archivo(imagen, carpeta_id, imagen.filename)

    producto = Producto(
        asociacion_id=current_user.id,
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        disponible=disponible,
        imagen_file_id=imagen_file_id,
    )
    db.add(producto)
    db.commit()

    return RedirectResponse(url="/productos", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/productos/editar/{id}")
def editar_producto_form(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Asociacion = Depends(current_user_dependency),
):
    producto = (
        db.query(Producto)
        .filter(Producto.id == id, Producto.asociacion_id == current_user.id)
        .first()
    )
    return templates.TemplateResponse(
        "editar_producto.html",
        {"request": request, "usuario": current_user, "producto": producto},
    )


@router.post("/productos/editar/{id}")
async def editar_producto_post(
    id: int,
    request: Request,
    nombre: str = Form(...),
    descripcion: str = Form(None),
    precio: int = Form(None),
    disponible: int = Form(1),
    imagen: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: Asociacion = Depends(current_user_dependency),
):
    producto = (
        db.query(Producto)
        .filter(Producto.id == id, Producto.asociacion_id == current_user.id)
        .first()
    )

    if not producto:
        return RedirectResponse(url="/productos", status_code=status.HTTP_303_SEE_OTHER)

    producto.nombre = nombre
    producto.descripcion = descripcion
    producto.precio = precio
    producto.disponible = disponible

    if imagen and imagen.filename:
        carpeta_id = crear_carpeta_si_no_existe(f"asociacion_{current_user.id}")
        nueva_imagen_file_id = await subir_archivo(imagen, carpeta_id, imagen.filename)
        if producto.imagen_file_id:
            try:
                eliminar_archivo(producto.imagen_file_id)
            except Exception:
                pass
        producto.imagen_file_id = nueva_imagen_file_id

    db.commit()
    return RedirectResponse(url="/productos", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/productos/eliminar/{id}")
def eliminar_producto(
    id: int,
    db: Session = Depends(get_db),
    current_user: Asociacion = Depends(current_user_dependency),
):
    producto = (
        db.query(Producto)
        .filter(Producto.id == id, Producto.asociacion_id == current_user.id)
        .first()
    )

    if producto:
        if producto.imagen_file_id:
            try:
                eliminar_archivo(producto.imagen_file_id)
            except Exception:
                pass
        db.delete(producto)
        db.commit()

    return RedirectResponse(url="/productos", status_code=status.HTTP_303_SEE_OTHER)
