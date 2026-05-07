from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models import Producto, Valoracion, Noticia, Asociacion


def obtener_actividades_recientes(db: Session, limite: int = 15) -> list:
    """
    Devuelve actividades públicas para el feed social:
    - Productos nuevos verificados
    - Valoraciones recientes
    - Noticias publicadas
    Los acuerdos (pedidos aceptados) son privados y se manejan por notificaciones.
    """
    actividades = []

    # 1. Productos nuevos verificados
    productos = (
        db.query(Producto)
        .join(Asociacion)
        .filter(Asociacion.verificado == "1")
        .order_by(desc(Producto.fecha_creacion))
        .limit(5)
        .all()
    )
    for p in productos:
        actividades.append({
            "tipo": "producto",
            "icono": "🛒",
            "texto": f"{p.asociacion.nombre} publicó {p.nombre}",
            "descripcion": p.descripcion[:120] + "..." if len(p.descripcion) > 120 else p.descripcion,
            "fecha": p.fecha_creacion,
            "url": f"/asociacion/{p.asociacion.email}",
            "imagen": p.imagen_url
        })

    # 2. Valoraciones recientes
    valoraciones = (
        db.query(Valoracion)
        .order_by(desc(Valoracion.fecha))
        .limit(5)
        .all()
    )
    for v in valoraciones:
        estrellas = "⭐" * v.estrellas
        actividades.append({
            "tipo": "valoracion",
            "icono": "🌟",
            "texto": f"Valoración para {v.producto.nombre}",
            "descripcion": f"{estrellas} | {v.comentario[:120] if v.comentario else 'Sin comentario'}",
            "fecha": v.fecha,
            "url": f"/catalogo?q={v.producto.nombre}",
            "imagen": v.producto.imagen_url
        })

    # 3. Noticias
    noticias = (
        db.query(Noticia)
        .order_by(desc(Noticia.fecha_publicacion))
        .limit(5)
        .all()
    )
    for n in noticias:
        actividades.append({
            "tipo": "noticia",
            "icono": "📰",
            "texto": n.titulo,
            "descripcion": n.contenido[:120] + "..." if len(n.contenido) > 120 else n.contenido,
            "fecha": n.fecha_publicacion,
            "url": f"/noticias/{n.id}",
            "imagen": n.imagen_url
        })

    # Ordenar todo por fecha descendente
    actividades.sort(key=lambda x: x["fecha"] if x["fecha"] else datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return actividades[:limite]