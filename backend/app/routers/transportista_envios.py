from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.services.transporte_service import listar_envios_transportista, actualizar_estado_envio
from app.templates import templates

router = APIRouter(prefix="/mis-envios", tags=["transportista"])

@router.get("/", response_class=HTMLResponse)
def mis_envios(request: Request, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if not current_user or current_user.get("tipo") != "transportista":
        return RedirectResponse(url="/auth/login", status_code=303)

    envios = listar_envios_transportista(db, current_user["email"])
    return templates.TemplateResponse("mis_envios.html", {
        "request": request,
        "envios": envios,
    })

@router.post("/actualizar-estado")
def actualizar_estado(request: Request, pedido_id: str = Form(...), nuevo_estado: str = Form(...), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if not current_user or current_user.get("tipo") != "transportista":
        return RedirectResponse(url="/auth/login", status_code=303)

    from app.models import Transportista
    transportista = db.query(Transportista).filter(Transportista.email == current_user["email"]).first()
    if transportista:
        actualizar_estado_envio(db, pedido_id, transportista.id, nuevo_estado)
    return RedirectResponse(url="/mis-envios", status_code=303)