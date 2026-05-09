from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.templates import templates
from app.models import Asociacion, Persona, Transportista, ValoracionComprador, Producto

router = APIRouter()

@router.get("/perfil", response_class=HTMLResponse)
def mi_perfil(request: Request, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)
    
    tipo = current_user.get("tipo")
    email = current_user["email"]

    if tipo == "transportista":
        return RedirectResponse(url="/perfil-transportista", status_code=303)
    
    if tipo == "persona":
        persona = db.query(Persona).filter(Persona.email == email).first()
        valoraciones = db.query(ValoracionComprador).filter(ValoracionComprador.comprador_email == email).all()
        return templates.TemplateResponse("perfil_persona.html", {
            "request": request, 
            "persona": persona or current_user,
            "valoraciones": valoraciones
        })
    
    # asociación u otro
    return RedirectResponse(url="/panel", status_code=303)


@router.get("/perfil/{email}", response_class=HTMLResponse)
def perfil_publico(request: Request, email: str, db: Session = Depends(get_db)):
    """
    Muestra el perfil público de cualquier usuario (asociación, persona, transportista).
    """
    # Intentar encontrar en cada tipo
    asociacion = db.query(Asociacion).filter(Asociacion.email == email, Asociacion.verificado == "1").first()
    if asociacion:
        productos = [{"nombre": p.nombre, "descripcion": p.descripcion, "precio": p.precio, "imagen": p.imagen_url or "https://placehold.co/300x200/5B8C51/white?text=Producto", "tipo": p.tipo, "tipo_precio": p.tipo_precio} for p in asociacion.productos]
        return templates.TemplateResponse("perfil_publico.html", {
            "request": request,
            "usuario": {
                "email": asociacion.email,
                "nombre": asociacion.nombre,
                "tipo": "asociacion",
                "descripcion": asociacion.descripcion,
                "direccion": asociacion.direccion,
                "telefono": asociacion.telefono,
                "logo_url": asociacion.logo_url,
                "show_whatsapp": asociacion.show_whatsapp,
                "productos": productos
            }
        })

    persona = db.query(Persona).filter(Persona.email == email).first()
    if persona:
        valoraciones = db.query(ValoracionComprador).filter(ValoracionComprador.comprador_email == email).all()
        return templates.TemplateResponse("perfil_publico.html", {
            "request": request,
            "usuario": {
                "email": persona.email,
                "nombre": persona.nombre,
                "tipo": "persona",
                "telefono": persona.telefono,
                "hoja_vida_url": persona.hoja_vida_url,
                "valoraciones": valoraciones
            }
        })

    transportista = db.query(Transportista).filter(Transportista.email == email).first()
    if transportista:
        return templates.TemplateResponse("perfil_publico.html", {
            "request": request,
            "usuario": {
                "email": transportista.email,
                "nombre": transportista.nombre,
                "tipo": "transportista",
                "telefono": transportista.telefono,
                "tipo_vehiculo": transportista.tipo_vehiculo,
                "capacidad": transportista.capacidad,
                "zona_cobertura": transportista.zona_cobertura,
                "tarifa_base": transportista.tarifa_base,
                "costo_km": transportista.costo_km,
                "documento_url": transportista.documento_url
            }
        })

    # No encontrado
    return RedirectResponse(url="/catalogo", status_code=303)