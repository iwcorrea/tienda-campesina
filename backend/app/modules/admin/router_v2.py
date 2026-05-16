from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.models import Pedido, Asociacion, Persona, Transportista
from app.modules.billing.models import Commission

router = APIRouter(prefix="/admin", tags=["admin_v2"])

def is_admin(current_user: dict):
    if current_user["tipo"] != "admin":
        raise HTTPException(status_code=403, detail="Requiere rol admin")

@router.get("/stats")
def admin_stats(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    is_admin(current_user)
    return {
        "total_pedidos": db.query(Pedido).count(),
        "total_comisiones": db.query(Commission).count(),
        "total_usuarios": db.query(Asociacion).count() + db.query(Persona).count() + db.query(Transportista).count(),
    }

@router.get("/users")
def admin_users(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    is_admin(current_user)
    # simplificado: lista de asociaciones
    return db.query(Asociacion).all()

@router.get("/commissions")
def admin_commissions(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    is_admin(current_user)
    return db.query(Commission).order_by(Commission.created_at.desc()).limit(100).all()