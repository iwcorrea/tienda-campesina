from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Asociacion

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/asociacion/{email}", response_class=HTMLResponse)
def perfil_asociacion(request: Request, email: str, db: Session = Depends(get_db)):
    a = db.query(Asociacion).filter(Asociacion.email == email, Asociacion.verificado == "1").first()
    if not a:
        return RedirectResponse(url="/catalogo", status_code=303)
    productos = []
    for p in a.productos:
        productos.append({
            "nombre": p.nombre,
            "descripcion": p.descripcion,
            "precio": p.precio,
            "imagen": p.imagen_url or "https://placehold.co/300x200/5B8C51/white?text=Producto",
            "tipo": p.tipo,
            "tipo_precio": p.tipo_precio
        })
    asociacion = {
        "email": a.email,
        "nombre": a.nombre,
        "descripcion": a.descripcion,
        "direccion": a.direccion,
        "telefono": a.telefono,
        "logo_url": a.logo_url,
        "show_whatsapp": a.show_whatsapp
    }
    return templates.TemplateResponse("perfil.html", {"request": request, "asociacion": asociacion, "productos": productos})