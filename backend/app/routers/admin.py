import logging
from fastapi import APIRouter, Request, Form, File, UploadFile, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.services.admin_service import (
    obtener_totales_admin,
    obtener_registros_mensuales,
    obtener_ultimas_asociaciones,
    obtener_ultimas_vacantes,
    listar_asociaciones_admin,
    toggle_verificacion_asociacion,
    obtener_asociacion_por_email,
    obtener_producto_por_id,
    actualizar_producto_admin,
    obtener_configuracion,
    actualizar_configuracion,
)
from app.viewmodels.admin import AsociacionAdminViewModel, ProductoAdminViewModel
from app.templates import templates
import cloudinary
import cloudinary.api
import cloudinary.uploader

router = APIRouter()
logger = logging.getLogger("admin")

ADMIN_EMAILS = {"admin@example.com"}   # Ajustá según tu lógica de admin

def es_admin(request: Request) -> bool:
    # Podés usar request.session.get("es_admin") si ya existe, o verificar email
    return request.session.get("es_admin", False) or request.session.get("usuario") in ADMIN_EMAILS


# ─── DASHBOARD ──────────────────────────────────────
@router.get("/admin", response_class=HTMLResponse)
def admin_dashboard(
    request: Request,
    db: Session = Depends(get_db),
):
    if not es_admin(request):
        return RedirectResponse(url="/auth/login", status_code=303)

    totales = obtener_totales_admin(db)
    labels_mes, data_mensual = obtener_registros_mensuales(db)
    ultimas_asoc = obtener_ultimas_asociaciones(db)
    ultimas_vac = obtener_ultimas_vacantes(db)

    asoc_vm = [AsociacionAdminViewModel.from_orm(a) for a in ultimas_asoc]

    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "total_asociaciones": totales["total_asociaciones"],
        "total_productos": totales["total_productos"],
        "total_personas": totales["total_personas"],
        "total_vacantes": totales["total_vacantes"],
        "labels_mes": labels_mes,
        "data_mensual": data_mensual,
        "ultimas_asociaciones": asoc_vm,
        "ultimas_vacantes": ultimas_vac,
    })


# ─── LISTA DE ASOCIACIONES ─────────────────────────
@router.get("/admin/asociaciones", response_class=HTMLResponse)
def admin_lista_asociaciones(
    request: Request,
    db: Session = Depends(get_db),
):
    if not es_admin(request):
        return RedirectResponse(url="/auth/login", status_code=303)

    asociaciones = listar_asociaciones_admin(db)
    data = [AsociacionAdminViewModel.from_orm(a) for a in asociaciones]
    return templates.TemplateResponse("admin_asociaciones.html", {"request": request, "asociaciones": data})


@router.post("/admin/toggle-estado/{email}")
def admin_toggle_estado(
    request: Request,
    email: str,
    db: Session = Depends(get_db),
):
    if not es_admin(request):
        return RedirectResponse(url="/auth/login", status_code=303)

    toggle_verificacion_asociacion(db, email)
    return RedirectResponse(url="/admin/asociaciones", status_code=303)


# ─── GESTIÓN DE ARCHIVOS ───────────────────────────
@router.get("/admin/archivos", response_class=HTMLResponse)
def admin_archivos(
    request: Request,
    resource_type: str = "image",
    next_cursor: str = None,
):
    if not es_admin(request):
        return RedirectResponse(url="/auth/login", status_code=303)

    recursos = []
    cursor = None
    try:
        result = cloudinary.api.resources(
            type="upload",
            resource_type=resource_type,
            max_results=50,
            next_cursor=next_cursor,
        )
        recursos = result.get("resources", [])
        cursor = result.get("next_cursor", None)
    except Exception as e:
        logger.exception("Error listando archivos")

    return templates.TemplateResponse("admin_archivos.html", {
        "request": request,
        "recursos": recursos,
        "resource_type": resource_type,
        "next_cursor": cursor,
    })


@router.post("/admin/archivos/eliminar")
def admin_eliminar_archivo(
    request: Request,
    public_id: str = Form(...),
    resource_type: str = Form(...),
):
    if not es_admin(request):
        return RedirectResponse(url="/auth/login", status_code=303)

    cloudinary.uploader.destroy(public_id, resource_type=resource_type)
    return RedirectResponse(url=f"/admin/archivos?resource_type={resource_type}", status_code=303)


# ─── EDITAR ASOCIACIÓN ─────────────────────────────
@router.get("/admin/asociacion/{email}/editar", response_class=HTMLResponse)
def admin_editar_asociacion_form(
    request: Request,
    email: str,
    db: Session = Depends(get_db),
):
    if not es_admin(request):
        return RedirectResponse(url="/auth/login", status_code=303)

    a = obtener_asociacion_por_email(db, email)
    if not a:
        return RedirectResponse(url="/admin/asociaciones", status_code=303)

    perfil = {
        "email": a.email,
        "nombre": a.nombre,
        "logo_url": a.logo_url,
        "camara_comercio_url": a.camara_url,
        "rut_url": a.rut_url,
    }
    return templates.TemplateResponse("admin_editar_asociacion.html", {"request": request, "perfil": perfil})


@router.post("/admin/asociacion/{email}/actualizar")
def admin_actualizar_asociacion(
    request: Request,
    email: str,
    logo_url: str = Form(""),
    camara_url: str = Form(""),
    rut_url: str = Form(""),
    db: Session = Depends(get_db),
):
    if not es_admin(request):
        return RedirectResponse(url="/auth/login", status_code=303)

    a = obtener_asociacion_por_email(db, email)
    if a:
        a.logo_url = logo_url.strip()
        a.camara_url = camara_url.strip()
        a.rut_url = rut_url.strip()
        db.commit()
    return RedirectResponse(url=f"/admin/asociacion/{email}/editar", status_code=303)


# ─── EDITAR PRODUCTO ───────────────────────────────
@router.get("/admin/producto/{producto_id}/editar", response_class=HTMLResponse)
def admin_editar_producto_form(
    request: Request,
    producto_id: str,
    db: Session = Depends(get_db),
):
    if not es_admin(request):
        return RedirectResponse(url="/auth/login", status_code=303)

    p = obtener_producto_por_id(db, producto_id)
    if not p:
        return RedirectResponse(url="/admin/asociaciones", status_code=303)

    producto_vm = ProductoAdminViewModel.from_orm(p)
    return templates.TemplateResponse("admin_editar_producto.html", {"request": request, "producto": producto_vm})


@router.post("/admin/producto/{producto_id}/actualizar")
def admin_actualizar_producto(
    request: Request,
    producto_id: str,
    imagen_url: str = Form(""),
    db: Session = Depends(get_db),
):
    if not es_admin(request):
        return RedirectResponse(url="/auth/login", status_code=303)

    actualizar_producto_admin(db, producto_id, imagen_url)
    return RedirectResponse(url=f"/admin/producto/{producto_id}/editar", status_code=303)


# ─── CONFIGURACIÓN AVANZADA ─────────────────────────
@router.get("/admin/configuracion", response_class=HTMLResponse)
def admin_configuracion_form(request: Request):
    if not es_admin(request):
        return RedirectResponse(url="/auth/login", status_code=303)

    config = request.state.config   # Ya lo carga el middleware
    return templates.TemplateResponse("admin_configuracion.html", {"request": request, "config": config})


@router.post("/admin/configuracion")
def admin_configuracion_guardar(
    request: Request,
    # SEO
    titulo_sitio: str = Form(...),
    descripcion_meta: str = Form(...),
    google_verification: str = Form(""),
    google_analytics_id: str = Form(""),
    robots_txt_extra: str = Form(""),
    # Diseño colores
    color_primario: str = Form(...),
    color_secundario: str = Form(...),
    color_fondo: str = Form(...),
    color_texto: str = Form(...),
    color_enlaces: str = Form(...),
    color_fondo_tarjetas: str = Form(...),
    color_hover: str = Form(...),
    # Tipografía
    fuente_nombre: str = Form(...),
    fuente_tamano_base: str = Form(...),
    fuente_url: str = Form(...),
    # CSS
    css_personalizado: str = Form(""),
    # Títulos / descripciones páginas
    titulo_inicio: str = Form(""),
    descripcion_inicio: str = Form(""),
    titulo_catalogo: str = Form(""),
    descripcion_catalogo: str = Form(""),
    titulo_bolsa: str = Form(""),
    descripcion_bolsa: str = Form(""),
    titulo_calculadora: str = Form(""),
    descripcion_calculadora: str = Form(""),
    # Contenidos (nuevos)
    inicio_titulo: str = Form(""),
    inicio_subtitulo: str = Form(""),
    inicio_titulo_tarjeta: str = Form(""),
    inicio_texto_tarjeta: str = Form(""),
    footer_texto: str = Form(""),
    footer_subtexto: str = Form(""),
    menu_mostrar_catalogo: str = Form(""),
    menu_mostrar_calculadora: str = Form(""),
    menu_mostrar_bolsa: str = Form(""),
    menu_enlace_extra: str = Form(""),
    menu_url_extra: str = Form(""),
    # Archivos
    logo: UploadFile = File(None),
    favicon_32: UploadFile = File(None),
    favicon_16: UploadFile = File(None),
    imagen_og: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    if not es_admin(request):
        return RedirectResponse(url="/auth/login", status_code=303)

    # Subir archivos si existen
    logo_url = upload_file_cloudinary_admin(logo, "config") if logo and logo.filename else ""
    favicon32 = upload_file_cloudinary_admin(favicon_32, "config") if favicon_32 and favicon_32.filename else ""
    favicon16 = upload_file_cloudinary_admin(favicon_16, "config") if favicon_16 and favicon_16.filename else ""
    og_url = upload_file_cloudinary_admin(imagen_og, "config") if imagen_og and imagen_og.filename else ""

    # Diccionario con todos los campos de texto
    data = {
        "titulo_sitio": titulo_sitio.strip(),
        "descripcion_meta": descripcion_meta.strip(),
        "google_verification": google_verification.strip(),
        "google_analytics_id": google_analytics_id.strip(),
        "robots_txt_extra": robots_txt_extra.strip(),
        "color_primario": color_primario.strip(),
        "color_secundario": color_secundario.strip(),
        "color_fondo": color_fondo.strip(),
        "color_texto": color_texto.strip(),
        "color_enlaces": color_enlaces.strip(),
        "color_fondo_tarjetas": color_fondo_tarjetas.strip(),
        "color_hover": color_hover.strip(),
        "fuente_nombre": fuente_nombre.strip(),
        "fuente_tamano_base": fuente_tamano_base.strip(),
        "fuente_url": fuente_url.strip() if "http" in fuente_url else "",
        "css_personalizado": css_personalizado.strip(),
        "titulo_inicio": titulo_inicio.strip(),
        "descripcion_inicio": descripcion_inicio.strip(),
        "titulo_catalogo": titulo_catalogo.strip(),
        "descripcion_catalogo": descripcion_catalogo.strip(),
        "titulo_bolsa": titulo_bolsa.strip(),
        "descripcion_bolsa": descripcion_bolsa.strip(),
        "titulo_calculadora": titulo_calculadora.strip(),
        "descripcion_calculadora": descripcion_calculadora.strip(),
        "inicio_titulo": inicio_titulo.strip(),
        "inicio_subtitulo": inicio_subtitulo.strip(),
        "inicio_titulo_tarjeta": inicio_titulo_tarjeta.strip(),
        "inicio_texto_tarjeta": inicio_texto_tarjeta.strip(),
        "footer_texto": footer_texto.strip(),
        "footer_subtexto": footer_subtexto.strip(),
        "menu_mostrar_catalogo": menu_mostrar_catalogo.strip(),
        "menu_mostrar_calculadora": menu_mostrar_calculadora.strip(),
        "menu_mostrar_bolsa": menu_mostrar_bolsa.strip(),
        "menu_enlace_extra": menu_enlace_extra.strip(),
        "menu_url_extra": menu_url_extra.strip(),
    }

    actualizar_configuracion(db, data, logo_url, favicon32, favicon16, og_url)
    return RedirectResponse(url="/admin/configuracion", status_code=303)


def upload_file_cloudinary_admin(file: UploadFile, folder: str) -> str:
    if not file or not file.filename:
        return ""
    try:
        result = cloudinary.uploader.upload(
            file.file,
            folder=folder,
            filename=file.filename,
            use_filename=True,
            unique_filename=True,
            access_mode="public"
        )
        return result.get("secure_url", "")
    except Exception:
        return ""