from fastapi import APIRouter, Request, Form, File, UploadFile, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.services.noticia_service import (
    listar_noticias_admin,
    listar_noticias_publico,
    obtener_noticia_por_id,
    crear_noticia,
    actualizar_noticia,
    eliminar_noticia,
)
from app.viewmodels.noticia import NoticiaViewModel
from app.templates import templates

router = APIRouter()


def es_admin(request: Request) -> bool:
    return request.session.get("es_admin", False)


@router.get("/admin/noticias", response_class=HTMLResponse)
def admin_noticias(
    request: Request,
    db: Session = Depends(get_db),
):
    if not es_admin(request):
        return RedirectResponse(url="/auth/login", status_code=303)

    noticias_orm = listar_noticias_admin(db)
    noticias_vm = [NoticiaViewModel.from_orm(n) for n in noticias_orm]
    return templates.TemplateResponse("admin_noticias.html", {
        "request": request,
        "noticias": noticias_vm,
    })


@router.get("/admin/noticias/nueva", response_class=HTMLResponse)
def admin_noticia_nueva(request: Request):
    if not es_admin(request):
        return RedirectResponse(url="/auth/login", status_code=303)
    return templates.TemplateResponse("admin_noticia_form.html", {"request": request})


@router.post("/admin/noticias/nueva")
def admin_noticia_crear(
    request: Request,
    titulo: str = Form(...),
    contenido: str = Form(...),
    imagen: UploadFile = File(None),
    fecha_publicacion: str = Form(None),
    db: Session = Depends(get_db),
):
    if not es_admin(request):
        return RedirectResponse(url="/auth/login", status_code=303)

    crear_noticia(db, titulo, contenido, imagen, fecha_publicacion)
    return RedirectResponse(url="/admin/noticias", status_code=303)


@router.get("/admin/noticias/editar/{noticia_id}", response_class=HTMLResponse)
def admin_noticia_editar(
    request: Request,
    noticia_id: str,
    db: Session = Depends(get_db),
):
    if not es_admin(request):
        return RedirectResponse(url="/auth/login", status_code=303)

    noticia = obtener_noticia_por_id(db, noticia_id)
    if not noticia:
        return RedirectResponse(url="/admin/noticias", status_code=303)

    return templates.TemplateResponse("admin_noticia_form.html", {
        "request": request,
        "noticia": noticia,
    })


@router.post("/admin/noticias/editar/{noticia_id}")
def admin_noticia_actualizar(
    request: Request,
    noticia_id: str,
    titulo: str = Form(...),
    contenido: str = Form(...),
    imagen: UploadFile = File(None),
    fecha_publicacion: str = Form(None),
    db: Session = Depends(get_db),
):
    if not es_admin(request):
        return RedirectResponse(url="/auth/login", status_code=303)

    actualizar_noticia(db, noticia_id, titulo, contenido, imagen, fecha_publicacion)
    return RedirectResponse(url="/admin/noticias", status_code=303)


@router.post("/admin/noticias/eliminar/{noticia_id}")
def admin_noticia_eliminar(
    request: Request,
    noticia_id: str,
    db: Session = Depends(get_db),
):
    if not es_admin(request):
        return RedirectResponse(url="/auth/login", status_code=303)

    eliminar_noticia(db, noticia_id)
    return RedirectResponse(url="/admin/noticias", status_code=303)


@router.get("/noticias", response_class=HTMLResponse)
def noticias_publico(
    request: Request,
    db: Session = Depends(get_db),
):
    noticias_orm = listar_noticias_publico(db)
    noticias_vm = [NoticiaViewModel.from_orm(n) for n in noticias_orm]
    return templates.TemplateResponse("noticias.html", {
        "request": request,
        "noticias": noticias_vm,
    })


@router.get("/noticias/{noticia_id}", response_class=HTMLResponse)
def noticia_detalle(
    request: Request,
    noticia_id: str,
    db: Session = Depends(get_db),
):
    noticia = obtener_noticia_por_id(db, noticia_id)
    if not noticia:
        return RedirectResponse(url="/noticias", status_code=303)

    noticia_vm = NoticiaViewModel.from_orm(noticia)
    return templates.TemplateResponse("noticia_detalle.html", {
        "request": request,
        "noticia": noticia_vm,
    })