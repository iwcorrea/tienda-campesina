"""
Router del módulo documents.
Proporciona endpoints para consultar documentos de un pedido y visualizarlos.
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.dependencies import get_current_user
from app.modules.documents.service import obtener_documentos_pedido
from app.modules.documents.dependencies import get_db

router = APIRouter(prefix="/documentos", tags=["documentos"])

@router.get("/pedido/{pedido_id}", response_class=HTMLResponse)
def listar_documentos_pedido(
    request: Request,
    pedido_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Muestra los documentos generados para un pedido específico."""
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    documentos = obtener_documentos_pedido(db, pedido_id)
    # Aquí se podría renderizar una plantilla, pero por ahora devolvemos JSON
    # o una lista simple. En el futuro se integrará con la UI.
    from fastapi.responses import JSONResponse
    return JSONResponse([
        {
            "id": d.id,
            "tipo": d.tipo,
            "storage_url": d.storage_url,
            "fecha": d.fecha_generacion.strftime("%d/%m/%Y %H:%M") if d.fecha_generacion else "",
            "estado": d.estado,
            "version": d.version,
        }
        for d in documentos
    ])