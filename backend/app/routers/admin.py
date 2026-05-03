import logging
from fastapi import APIRouter, Request, Form, File, UploadFile, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from app.database import get_db
from app.models import Asociacion, Producto, Persona, Vacante, Configuracion
import cloudinary
import cloudinary.api
import cloudinary.uploader
import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger("admin")

# ─── DASHBOARD ──────────────────────────────────────
@router.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("es_admin"):
        return RedirectResponse(url="/auth/login", status_code=303)

    total_asociaciones = db.query(func.count(Asociacion.id)).scalar()
    total_productos = db.query(func.count(Producto.id)).scalar()
    total_personas = db.query(func.count(Persona.id)).scalar()
    total_vacantes = db.query(func.count(Vacante.id)).filter(Vacante.fecha_limite >= datetime.datetime.now()).scalar()

    labels_mes = []
    data_mensual = []
    hoy = datetime.date.today()
    meses_nombres = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    for i in range(5, -1, -1):
        mes = hoy.month - i
        anio = hoy.year
        if mes <= 0:
            mes += 12
            anio -= 1
        conteo = db.query(func.count(Asociacion.id)).filter(
            extract('year', Asociacion.fecha_registro) == anio,
            extract('month', Asociacion.fecha_registro) == mes
        ).scalar()
        data_mensual.append(conteo)
        labels_mes.append(f"{meses_nombres[mes-1]} {str(anio)[-2:]}")

    ultimas_asociaciones = db.query(Asociacion).order_by(Asociacion.fecha_registro.desc()).limit(5).all()
    ultimas_vacantes = db.query(Vacante).order_by(Vacante.fecha_publicacion.desc()).limit(5).all()

    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "total_asociaciones": total_asociaciones,
        "total_productos": total_productos,
        "total_personas": total_personas,
        "total_vacantes": total_vacantes,
        "labels_mes": labels_mes,
        "data_mensual": data_mensual,
        "ultimas_asociaciones": ultimas_asociaciones,
        "ultimas_vacantes": ultimas_vacantes
    })

# ─── LISTA DE ASOCIACIONES ─────────────────────────
@router.get("/admin/asociaciones", response_class=HTMLResponse)
def admin_lista_asociaciones(request: Request, db: Session = Depends(get_db)):
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
    return templates.TemplateResponse("admin_asociaciones.html", {"request": request, "asociaciones": data})

@router.post("/admin/toggle-estado/{email}")
def admin_toggle_estado(request: Request, email: str, db: Session = Depends(get_db)):
    if not request.session.get("es_admin"):
        return RedirectResponse(url="/auth/login", status_code=303)
    a = db.query(Asociacion).filter(Asociacion.email == email).first()
    if a:
        a.verificado = "" if a.verificado == "1" else "1"
        db.commit()
    return RedirectResponse(url="/admin/asociaciones", status_code=303)

# ─── GESTIÓN DE ARCHIVOS ───────────────────────────
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
def admin_eliminar_archivo(request: Request, public_id: str = Form(...), resource_type: str = Form(...)):
    if not request.session.get("es_admin"):
        return RedirectResponse(url="/auth/login", status_code=303)
    cloudinary.uploader.destroy(public_id, resource_type=resource_type)
    return RedirectResponse(url=f"/admin/archivos?resource_type={resource_type}", status_code=303)

# ─── EDITAR ASOCIACIÓN ─────────────────────────────
@router.get("/admin/asociacion/{email}/editar", response_class=HTMLResponse)
def admin_editar_asociacion_form(request: Request, email: str, db: Session = Depends(get_db)):
    if not request.session.get("es_admin"):
        return RedirectResponse(url="/auth/login", status_code=303)
    a = db.query(Asociacion).filter(Asociacion.email == email).first()
    if not a:
        return RedirectResponse(url="/admin/asociaciones", status_code=303)
    perfil = {"email": a.email, "nombre": a.nombre, "logo_url": a.logo_url, "camara_comercio_url": a.camara_url, "rut_url": a.rut_url}
    return templates.TemplateResponse("admin_editar_asociacion.html", {"request": request, "perfil": perfil})

@router.post("/admin/asociacion/{email}/actualizar")
def admin_actualizar_asociacion(request: Request, email: str, logo_url: str = Form(""), camara_url: str = Form(""), rut_url: str = Form(""), db: Session = Depends(get_db)):
    if not request.session.get("es_admin"):
        return RedirectResponse(url="/auth/login", status_code=303)
    a = db.query(Asociacion).filter(Asociacion.email == email).first()
    if a:
        a.logo_url = logo_url.strip()
        a.camara_url = camara_url.strip()
        a.rut_url = rut_url.strip()
        db.commit()
    return RedirectResponse(url=f"/admin/asociacion/{email}/editar", status_code=303)

# ─── EDITAR PRODUCTO ───────────────────────────────
@router.get("/admin/producto/{producto_id}/editar", response_class=HTMLResponse)
def admin_editar_producto_form(request: Request, producto_id: str, db: Session = Depends(get_db)):
    if not request.session.get("es_admin"):
        return RedirectResponse(url="/auth/login", status_code=303)
    p = db.query(Producto).filter(Producto.id == producto_id).first()
    if not p:
        return RedirectResponse(url="/admin/asociaciones", status_code=303)
    producto = {"id": p.id, "nombre": p.nombre, "precio": p.precio, "imagen_url": p.imagen_url}
    return templates.TemplateResponse("admin_editar_producto.html", {"request": request, "producto": producto})

@router.post("/admin/producto/{producto_id}/actualizar")
def admin_actualizar_producto(request: Request, producto_id: str, imagen_url: str = Form(""), db: Session = Depends(get_db)):
    if not request.session.get("es_admin"):
        return RedirectResponse(url="/auth/login", status_code=303)
    p = db.query(Producto).filter(Producto.id == producto_id).first()
    if p:
        p.imagen_url = imagen_url.strip()
        db.commit()
    return RedirectResponse(url=f"/admin/producto/{producto_id}/editar", status_code=303)

# ─── CONFIGURACIÓN AVANZADA ─────────────────────────
@router.get("/admin/configuracion", response_class=HTMLResponse)
def admin_configuracion_form(request: Request):
    if not request.session.get("es_admin"):
        return RedirectResponse(url="/auth/login", status_code=303)
    config = request.state.config
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
    db: Session = Depends(get_db)
):
    if not request.session.get("es_admin"):
        return RedirectResponse(url="/auth/login", status_code=303)
    config = db.query(Configuracion).first()
    if not config:
        config = Configuracion()
        db.add(config)
    # Actualizar campos
    config.titulo_sitio = titulo_sitio.strip()
    config.descripcion_meta = descripcion_meta.strip()
    config.google_verification = google_verification.strip()
    config.google_analytics_id = google_analytics_id.strip()
    config.robots_txt_extra = robots_txt_extra.strip()
    config.color_primario = color_primario.strip()
    config.color_secundario = color_secundario.strip()
    config.color_fondo = color_fondo.strip()
    config.color_texto = color_texto.strip()
    config.color_enlaces = color_enlaces.strip()
    config.color_fondo_tarjetas = color_fondo_tarjetas.strip()
    config.color_hover = color_hover.strip()
    config.fuente_nombre = fuente_nombre.strip()
    config.fuente_tamano_base = fuente_tamano_base.strip()
    config.fuente_url = fuente_url.strip() if "http" in fuente_url else ""
    config.css_personalizado = css_personalizado.strip()
    config.titulo_inicio = titulo_inicio.strip()
    config.descripcion_inicio = descripcion_inicio.strip()
    config.titulo_catalogo = titulo_catalogo.strip()
    config.descripcion_catalogo = descripcion_catalogo.strip()
    config.titulo_bolsa = titulo_bolsa.strip()
    config.descripcion_bolsa = descripcion_bolsa.strip()
    config.titulo_calculadora = titulo_calculadora.strip()
    config.descripcion_calculadora = descripcion_calculadora.strip()
    config.inicio_titulo = inicio_titulo.strip()
    config.inicio_subtitulo = inicio_subtitulo.strip()
    config.inicio_titulo_tarjeta = inicio_titulo_tarjeta.strip()
    config.inicio_texto_tarjeta = inicio_texto_tarjeta.strip()
    config.footer_texto = footer_texto.strip()
    config.footer_subtexto = footer_subtexto.strip()
    config.menu_mostrar_catalogo = menu_mostrar_catalogo.strip()
    config.menu_mostrar_calculadora = menu_mostrar_calculadora.strip()
    config.menu_mostrar_bolsa = menu_mostrar_bolsa.strip()
    config.menu_enlace_extra = menu_enlace_extra.strip()
    config.menu_url_extra = menu_url_extra.strip()

    # Subir archivos a Cloudinary (si se proporcionan)
    if logo and logo.filename:
        config.logo_url = upload_file_cloudinary(logo, "config", raw=False)
    if favicon_32 and favicon_32.filename:
        config.favicon_32_url = upload_file_cloudinary(favicon_32, "config", raw=False)
    if favicon_16 and favicon_16.filename:
        config.favicon_16_url = upload_file_cloudinary(favicon_16, "config", raw=False)
    if imagen_og and imagen_og.filename:
        config.imagen_og_url = upload_file_cloudinary(imagen_og, "config", raw=False)

    db.commit()
    return RedirectResponse(url="/admin/configuracion", status_code=303)

def upload_file_cloudinary(file: UploadFile, folder: str, raw: bool = False):
    if not file or not file.filename:
        return ""
    try:
        kwargs = dict(folder=folder, filename=file.filename, use_filename=True, unique_filename=True, access_mode="public")
        if raw:
            kwargs["resource_type"] = "raw"
        result = cloudinary.uploader.upload(file.file, **kwargs)
        return result.get("secure_url", "")
    except Exception:
        return ""