import uuid
from typing import Optional
from sqlalchemy.orm import Session, selectinload
from app.models import Asociacion, Producto, Transportista, TransportistaFavorito, ItemPedido, RespuestaCotizacion
import cloudinary.uploader
from app.cloudinary_utils import delete_cloudinary_asset


def obtener_asociacion_y_productos(db: Session, email: str) -> Optional[Asociacion]:
    return db.query(Asociacion).filter(Asociacion.email == email).first()


def crear_producto(
    db: Session,
    email: str,
    nombre: str,
    descripcion: Optional[str],
    precio: int,
    tipo: str,
    tipo_precio: str,
    imagen_file=None,
) -> Producto:
    imagen_url = ""
    if imagen_file and imagen_file.filename:
        try:
            result = cloudinary.uploader.upload(
                imagen_file.file,
                folder="productos",
                filename=imagen_file.filename,
                use_filename=True,
                unique_filename=True,
                access_mode="public"
            )
            imagen_url = result.get("secure_url", "")
        except Exception:
            pass

    nuevo = Producto(
        id=str(uuid.uuid4()),
        asociacion_email=email,
        nombre=nombre,
        descripcion=descripcion or "",
        precio=precio,
        imagen_url=imagen_url,
        tipo=tipo,
        tipo_precio=tipo_precio,
    )
    db.add(nuevo)
    db.commit()
    return nuevo


def actualizar_producto(
    db: Session,
    email: str,
    producto_id: str,
    nombre: str,
    descripcion: Optional[str],
    precio: int,
    tipo: str,
    tipo_precio: str,
    imagen_file=None,
) -> Optional[Producto]:
    producto = db.query(Producto).filter(
        Producto.id == producto_id,
        Producto.asociacion_email == email
    ).first()
    if not producto:
        return None

    if imagen_file and imagen_file.filename:
        if producto.imagen_url:
            delete_cloudinary_asset(producto.imagen_url, resource_type="image")
        try:
            result = cloudinary.uploader.upload(
                imagen_file.file,
                folder="productos",
                filename=imagen_file.filename,
                use_filename=True,
                unique_filename=True,
                access_mode="public"
            )
            producto.imagen_url = result.get("secure_url", "")
        except Exception:
            pass

    producto.nombre = nombre
    producto.descripcion = descripcion or ""
    producto.precio = precio
    producto.tipo = tipo
    producto.tipo_precio = tipo_precio
    db.commit()
    return producto


def eliminar_producto(db: Session, email: str, producto_id: str) -> bool:
    producto = db.query(Producto).filter(
        Producto.id == producto_id,
        Producto.asociacion_email == email
    ).first()
    if not producto:
        return False
    if producto.imagen_url:
        delete_cloudinary_asset(producto.imagen_url, resource_type="image")
    db.delete(producto)
    db.commit()
    return True


# ─── TRANSPORTISTAS FAVORITOS ─────────────────────
def listar_favoritos(db: Session, email: str):
    favoritos = db.query(TransportistaFavorito).filter(
        TransportistaFavorito.asociacion_email == email
    ).all()
    todos = db.query(Transportista).filter(Transportista.activo == "1").all()
    return favoritos, todos


def agregar_favorito(db: Session, email: str, transportista_id: str) -> bool:
    existe = db.query(TransportistaFavorito).filter(
        TransportistaFavorito.asociacion_email == email,
        TransportistaFavorito.transportista_id == transportista_id
    ).first()
    if not existe:
        nuevo = TransportistaFavorito(
            asociacion_email=email,
            transportista_id=transportista_id
        )
        db.add(nuevo)
        db.commit()
        return True
    return False


def eliminar_favorito(db: Session, email: str, favorito_id: str) -> bool:
    fav = db.query(TransportistaFavorito).filter(
        TransportistaFavorito.id == favorito_id,
        TransportistaFavorito.asociacion_email == email
    ).first()
    if fav:
        db.delete(fav)
        db.commit()
        return True
    return False


# ─── COTIZACIONES ─────────────────────────────────
def obtener_items_cotizacion_asociacion(db: Session, email: str) -> list:
    items = (
        db.query(ItemPedido)
        .join(Producto)
        .options(
            selectinload(ItemPedido.producto),
            selectinload(ItemPedido.pedido)
        )
        .filter(Producto.asociacion_email == email)
        .order_by(ItemPedido.pedido_id.desc())
        .all()
    )
    resultado = []
    for item in items:
        resultado.append({
            "id": item.id,
            "producto": {"nombre": item.producto.nombre if item.producto else "Producto eliminado"},
            "pedido": {
                "id": item.pedido.id if item.pedido else "",
                "comprador_email": item.pedido.comprador_email if item.pedido else ""
            },
            "cantidad": item.cantidad,
            "precio_unitario_inicial": item.precio_unitario_inicial,
        })
    return resultado


def obtener_item_para_responder(db: Session, item_id: str, email_asociacion: str) -> Optional[ItemPedido]:
    return (
        db.query(ItemPedido)
        .join(Producto)
        .options(
            selectinload(ItemPedido.producto),
            selectinload(ItemPedido.pedido)
        )
        .filter(ItemPedido.id == item_id, Producto.asociacion_email == email_asociacion)
        .first()
    )


def guardar_respuesta_cotizacion(
    db: Session,
    item_id: str,
    email_asociacion: str,
    aceptado: str,
    precio_contraoferta: int = 0,
    cantidad_contraoferta: int = 0,
    fecha_entrega: str = "",
    mensaje: str = "",
) -> Optional[RespuestaCotizacion]:
    item = (
        db.query(ItemPedido)
        .join(Producto)
        .filter(ItemPedido.id == item_id, Producto.asociacion_email == email_asociacion)
        .first()
    )
    if not item:
        return None

    nueva = RespuestaCotizacion(
        item_pedido_id=item_id,
        asociacion_email=email_asociacion,
        aceptado=aceptado,
        precio_contraoferta=precio_contraoferta,
        cantidad_contraoferta=cantidad_contraoferta,
        fecha_entrega_contraoferta=fecha_entrega,
        mensaje=mensaje,
    )
    db.add(nueva)
    db.commit()
    return nueva