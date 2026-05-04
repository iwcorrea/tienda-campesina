import logging
import os
import uuid
from fastapi import APIRouter, Request, Form, File, UploadFile, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Asociacion, Producto, Transportista, TransportistaFavorito
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
def crear_producto(...): # sin cambios
    # (mantén todo igual que antes, lo omito por brevedad pero va igual)
    pass

# ─── EDITAR/ACTUALIZAR/ELIMINAR PRODUCTO (igual, sin cambios) ───
# ...

# ─── FAVORITOS DE TRANSPORTISTAS ─────────────────
@router.get("/panel/transportistas-favoritos", response_class=HTMLResponse)
def listar_favoritos(request: Request, db: Session = Depends(get_db)):
    if request.session.get("tipo_usuario") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    favoritos = db.query(TransportistaFavorito).filter(
        TransportistaFavorito.asociacion_email == email
    ).all()
    # Obtener todos los transportistas para poder agregar nuevos
    todos = db.query(Transportista).filter(Transportista.activo == "1").all()
    return templates.TemplateResponse("panel_transportistas_favoritos.html", {
        "request": request,
        "favoritos": favoritos,
        "transportistas": todos
    })

@router.post("/panel/transportistas-favoritos/agregar")
def agregar_favorito(
    request: Request,
    transportista_id: str = Form(...),
    db: Session = Depends(get_db)
):
    if request.session.get("tipo_usuario") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    # Verificar que no exista ya
    existe = db.query(TransportistaFavorito).filter(
        TransportistaFavorito.asociacion_email == email,
        TransportistaFavorito.transportista_id == transportista_id
    ).first()
    if not existe:
        nuevo = TransportistaFavorito(
            asociacion_email=email,
            transportista_id=transportista_id
        )
        db.add(nuevo)
        db.commit()
    return RedirectResponse(url="/panel/transportistas-favoritos", status_code=303)

@router.post("/panel/transportistas-favoritos/eliminar/{favorito_id}")
def eliminar_favorito(
    request: Request,
    favorito_id: str,
    db: Session = Depends(get_db)
):
    if request.session.get("tipo_usuario") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    fav = db.query(TransportistaFavorito).filter(
        TransportistaFavorito.id == favorito_id,
        TransportistaFavorito.asociacion_email == email
    ).first()
    if fav:
        db.delete(fav)
        db.commit()
    return RedirectResponse(url="/panel/transportistas-favoritos", status_code=303)

# ─── API PARA CALCULAR ENVÍO (ahora usa todos los transportistas activos) ─
@router.get("/api/calcular-envio/{asociacion_email}")
def calcular_envio(
    asociacion_email: str,
    distancia: float = Query(0),
    peso: float = Query(0),
    db: Session = Depends(get_db)
):
    # Ya no se usan transportadores propios, solo transportistas
    transportistas = db.query(Transportista).filter(Transportista.activo == "1").all()
    resultados = []
    for t in transportistas:
        costo = t.tarifa_base + (t.costo_km * distancia) + (peso * 200)
        resultados.append({
            "nombre": t.nombre,
            "medio": t.tipo_vehiculo,
            "telefono": t.telefono,
            "costo_estimado": round(costo),
            "tipo": "transportista"
        })
    return resultados