from sqlalchemy.orm import Session
from app.models import Producto

def listar_productos_catalogo(db: Session):
    """Retorna todos los productos activos."""
    return db.query(Producto).order_by(Producto.fecha_creacion.desc()).all()

def obtener_producto_por_id(db: Session, producto_id: str):
    """Retorna un producto por su ID."""
    return db.query(Producto).filter(Producto.id == producto_id).first()