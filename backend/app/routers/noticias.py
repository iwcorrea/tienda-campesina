import uuid
import datetime
from fastapi import APIRouter, Request, Form, File, UploadFile, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Noticia
import cloudinary.uploader

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def subir_imagen(file: UploadFile):
    if not file or not file.filename:
        return ""
    try:
        result = cloudinary.uploader.upload(
            file.file,
            folder="noticias",
            filename=file.filename,
            use_filename=True,
            unique_filename=True,
            access_mode="public"
        )
        return result.get("secure_url", "")
    except Exception:
        return ""

@router.get("/admin/noticias", response_class=HTMLResponse)
def admin_noticias(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("es_admin"):
        return RedirectResponse(url="/auth/login", status_code=303)
    noticias = db.query(Noticia).order_by(Noticia.fecha_publicacion.desc()).all()
    return templates.TemplateResponse("admin_noticias.html", {"request": request, "noticias": noticias})

@router.get("/admin/noticias/nueva", response_class=HTMLResponse)
def admin_noticia_nueva(request: Request):
    if not request.session.get("es_admin"):
        return RedirectResponse(url="/auth/login", status_code=303)
    return templates.TemplateResponse("admin_noticia_form.html", {"request": request})

@router.post("/admin/noticias/nueva")
def admin_noticia_crear(
    request: Request,
    titulo: str = Form(...),
    contenido: str = Form(...),
    imagen: UploadFile = File(None),
    fecha_publicacion: str = Form(None),
    db: Session = Depends(get_db)
):
    if not request.session.get("es_admin"):
        return RedirectResponse(url="/auth/login", status_code=303)
    imagen_url = subir_imagen(imagen)
    if fecha_publicacion and fecha_publicacion.strip():
        try:
            fecha = datetime.datetime.strptime(fecha_publicacion, "%Y-%m-%d")
        except:
            fecha = datetime.datetime.now(datetime.timezone.utc)
    else:
        fecha = datetime.datetime.now(datetime.timezone.utc)
    nueva = Noticia(
        id=str(uuid.uuid4()),
        titulo=titulo,
        contenido=contenido,
        imagen_url=imagen_url,
        fecha_publicacion=fecha
    )
    db.add(nueva)
    db.commit()
    return RedirectResponse(url="/admin/noticias", status_code=303)

@router.get("/admin/noticias/editar/{noticia_id}", response_class=HTMLResponse)
def admin_noticia_editar(request: Request, noticia_id: str, db: Session = Depends(get_db)):
    if not request.session.get("es_admin"):
        return RedirectResponse(url="/auth/login", status_code=303)
    noticia = db.query(Noticia).filter(Noticia.id == noticia_id).first()
    if not noticia:
        return RedirectResponse(url="/admin/noticias", status_code=303)
    return templates.TemplateResponse("admin_noticia_form.html", {"request": request, "noticia": noticia})

@router.post("/admin/noticias/editar/{noticia_id}")
def admin_noticia_actualizar(
    request: Request,
    noticia_id: str,
    titulo: str = Form(...),
    contenido: str = Form(...),
    imagen: UploadFile = File(None),
    fecha_publicacion: str = Form(None),
    db: Session = Depends(get_db)
):
    if not request.session.get("es_admin"):
        return RedirectResponse(url="/auth/login", status_code=303)
    noticia = db.query(Noticia).filter(Noticia.id == noticia_id).first()
    if not noticia:
        return RedirectResponse(url="/admin/noticias", status_code=303)
    noticia.titulo = titulo
    noticia.contenido = contenido
    if imagen and imagen.filename:
        if noticia.imagen_url:
            from app.main import delete_cloudinary_asset
            delete_cloudinary_asset(noticia.imagen_url, resource_type="image")
        noticia.imagen_url = subir_imagen(imagen)
    if fecha_publicacion and fecha_publicacion.strip():
        try:
            noticia.fecha_publicacion = datetime.datetime.strptime(fecha_publicacion, "%Y-%m-%d")
        except:
            pass
    db.commit()
    return RedirectResponse(url="/admin/noticias", status_code=303)

@router.post("/admin/noticias/eliminar/{noticia_id}")
def admin_noticia_eliminar(request: Request, noticia_id: str, db: Session = Depends(get_db)):
    if not request.session.get("es_admin"):
        return RedirectResponse(url="/auth/login", status_code=303)
    noticia = db.query(Noticia).filter(Noticia.id == noticia_id).first()
    if noticia:
        if noticia.imagen_url:
            from app.main import delete_cloudinary_asset
            delete_cloudinary_asset(noticia.imagen_url, resource_type="image")
        db.delete(noticia)
        db.commit()
    return RedirectResponse(url="/admin/noticias", status_code=303)

@router.get("/noticias", response_class=HTMLResponse)
def noticias_publico(request: Request, db: Session = Depends(get_db)):
    noticias = db.query(Noticia).order_by(Noticia.fecha_publicacion.desc()).all()
    return templates.TemplateResponse("noticias.html", {"request": request, "noticias": noticias})

@router.get("/noticias/{noticia_id}", response_class=HTMLResponse)
def noticia_detalle(request: Request, noticia_id: str, db: Session = Depends(get_db)):
    noticia = db.query(Noticia).filter(Noticia.id == noticia_id).first()
    if not noticia:
        return RedirectResponse(url="/noticias", status_code=303)
    return templates.TemplateResponse("noticia_detalle.html", {"request": request, "noticia": noticia})