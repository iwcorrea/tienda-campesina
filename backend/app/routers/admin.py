import logging
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Asociacion, Producto
import cloudinary
import cloudinary.api
import cloudinary.uploader

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger("admin")

@router.get("/admin", response_class=HTMLResponse)
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

@router.post("/admin/toggle-estado/{email}")
def admin_toggle_estado(request: Request, email: str, db: Session = Depends(get_db)):
    if not request.session.get("es_admin"):
        return RedirectResponse(url="/auth/login", status_code=303)
    a = db.query(Asociacion).filter(Asociacion.email == email).first()
    if a:
        a.verificado = "" if a.verificado == "1" else "1"
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@router.get("/admin/archivos", response_class=HTMLResponse)
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
        logger.exception("Error listando archivos")
    return templates.TemplateResponse("admin_archivos.html", {
        "request": request,
        "recursos": recursos,
        "resource_type": resource_type,
        "next_cursor": cursor
    })

@router.post("/admin/archivos/eliminar")
def admin_eliminar_archivo(
    request: Request,
    public_id: str = Form(...),
    resource_type: str = Form(...)
):
    if not request.session.get("es_admin"):
        return RedirectResponse(url="/auth/login", status_code=303)
    cloudinary.uploader.destroy(public_id, resource_type=resource_type)
    return RedirectResponse(url=f"/admin/archivos?resource_type={resource_type}", status_code=303)

@router.get("/admin/asociacion/{email}/editar", response_class=HTMLResponse)
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

@router.post("/admin/asociacion/{email}/actualizar")
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

@router.get("/admin/producto/{producto_id}/editar", response_class=HTMLResponse)
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

@router.post("/admin/producto/{producto_id}/actualizar")
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