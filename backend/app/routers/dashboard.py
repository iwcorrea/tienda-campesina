import logging
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import Asociacion, Producto, Valoracion, Mensaje, Vacante

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger("dashboard")

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    if "usuario" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    asociacion = db.query(Asociacion).filter(Asociacion.email == email).first()
    if not asociacion:
        return RedirectResponse(url="/auth/login", status_code=303)

    mis_productos = asociacion.productos
    total = len(mis_productos)
    productos_por_tipo = {"producto": 0, "servicio": 0}
    for p in mis_productos:
        prod_tipo = p.tipo or "producto"
        productos_por_tipo[prod_tipo] = productos_por_tipo.get(prod_tipo, 0) + 1

    ultimos = []
    for p in reversed(mis_productos[-5:]):
        ultimos.append({
            "nombre": p.nombre,
            "precio": p.precio,
            "imagen": p.imagen_url,
            "tipo": p.tipo,
            "tipo_precio": p.tipo_precio
        })

    # Valoraciones
    total_valoraciones = 0
    suma_estrellas = 0
    distribucion_estrellas = [0, 0, 0, 0, 0]
    ultimas_valoraciones = []
    try:
        all_vals = db.query(Valoracion).filter(Valoracion.producto_id.in_([p.id for p in mis_productos])).all()
        total_valoraciones = len(all_vals)
        for v in all_vals:
            est = v.estrellas
            suma_estrellas += est
            if 1 <= est <= 5:
                distribucion_estrellas[est - 1] += 1
        all_vals.sort(key=lambda x: x.fecha, reverse=True)
        for v in all_vals[:5]:
            prod = db.query(Producto).filter(Producto.id == v.producto_id).first()
            ultimas_valoraciones.append({
                "producto_nombre": prod.nombre if prod else "Producto",
                "estrellas": v.estrellas,
                "comentario": v.comentario or ""
            })
    except Exception:
        pass

    promedio_estrellas = round(suma_estrellas / total_valoraciones, 1) if total_valoraciones > 0 else 0

    # Mensajes
    total_mensajes = db.query(func.count(Mensaje.id)).filter(
        Mensaje.destinatario_email == email
    ).scalar()
    no_leidos = db.query(func.count(Mensaje.id)).filter(
        Mensaje.destinatario_email == email,
        Mensaje.leido == "0"
    ).scalar()
    ultimos_mensajes = db.query(Mensaje).filter(
        Mensaje.destinatario_email == email
    ).order_by(Mensaje.fecha_envio.desc()).limit(3).all()

    # Vacantes activas
    total_vacantes = db.query(func.count(Vacante.id)).filter(
        Vacante.asociacion_email == email,
        Vacante.fecha_limite >= func.now()
    ).scalar()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "usuario": asociacion.nombre,
        "total_productos": total,
        "ultimos_productos": ultimos,
        "productos_por_tipo": productos_por_tipo,
        "total_valoraciones": total_valoraciones,
        "promedio_estrellas": promedio_estrellas,
        "distribucion_estrellas": distribucion_estrellas,
        "ultimas_valoraciones": ultimas_valoraciones,
        "total_mensajes": total_mensajes,
        "no_leidos": no_leidos,
        "ultimos_mensajes": ultimos_mensajes,
        "total_vacantes": total_vacantes
    })