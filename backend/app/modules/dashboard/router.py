from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.templates import templates
from app.modules.dashboard.service import obtener_dashboard_data

router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    email = current_user["email"]
    tipo = current_user.get("tipo")
    data = obtener_dashboard_data(db, email, tipo)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "usuario": current_user.get("nombre_usuario", email),
        "tipo": tipo,
        **data,
    })

@router.get("/api/dashboard/metricas")
def api_metricas(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user:
        return JSONResponse([])
    data = obtener_dashboard_data(db, current_user["email"], current_user.get("tipo"))
    return JSONResponse(data["metricas"])

@router.get("/api/dashboard/pedidos")
def api_pedidos(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user:
        return JSONResponse([])
    from app.modules.dashboard.widgets import widget_pedidos_recientes
    pedidos = widget_pedidos_recientes(db, current_user["email"], current_user.get("tipo"))
    return JSONResponse(pedidos)

@router.get("/api/dashboard/timeline/{pedido_id}")
def api_timeline(
    pedido_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user:
        return JSONResponse([])
    from app.modules.dashboard.timeline import obtener_timeline
    timeline = obtener_timeline(db, pedido_id)
    return JSONResponse(timeline)