from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.modules.matching.service import obtener_recomendaciones

router = APIRouter(prefix="/matching", tags=["matching"])

@router.get("/recomendaciones")
def recomendaciones(
    request: Request,
    ubicacion: str = Query(""),
    tipo: str = Query("todos"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Endpoint para obtener recomendaciones personalizadas."""
    data = obtener_recomendaciones(db, ubicacion, tipo)
    return JSONResponse(data)