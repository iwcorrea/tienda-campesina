from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.services.dashboard_service import obtener_totales_dashboard, obtener_actividades_recientes
from app.viewmodels.dashboard import DashboardViewModel, ActividadViewModel
from app.templates import templates

router = APIRouter()


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user or current_user.get("tipo") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)

    email = current_user["email"]
    datos = obtener_totales_dashboard(db, email)
    if not datos:
        return RedirectResponse(url="/auth/login", status_code=303)

    productos_ids = [p.id for p in datos["asociacion"].productos]
    actividades_orm = obtener_actividades_recientes(db, email, productos_ids)

    actividades_vm = [ActividadViewModel(**a) for a in actividades_orm]

    vm = DashboardViewModel(
        usuario=datos["asociacion"].nombre,
        total_productos=datos["total_productos"],
        total_valoraciones=datos["total_valoraciones"],
        mensajes_pendientes=datos["mensajes_pendientes"],
        cotizaciones_pendientes=datos["cotizaciones_pendientes"],
        vacantes_activas=datos["vacantes_activas"],
        favoritos_count=datos["favoritos_count"],
        actividades=actividades_vm,
    )

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "usuario": vm.usuario,
        "total_productos": vm.total_productos,
        "total_valoraciones": vm.total_valoraciones,
        "mensajes_pendientes": vm.mensajes_pendientes,
        "cotizaciones_pendientes": vm.cotizaciones_pendientes,
        "vacantes_activas": vm.vacantes_activas,
        "favoritos_count": vm.favoritos_count,
        "actividades": [a.__dict__ for a in vm.actividades],
    })