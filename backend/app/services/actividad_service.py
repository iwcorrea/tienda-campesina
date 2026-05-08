from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models import Producto, Valoracion, Noticia, Asociacion
from app.utils import utc_to_colombia

def obtener_actividades_recientes(db: Session, limite: int = 15) -> list:
    actividades = []

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
            "fecha": utc_to_colombia(p.fecha_creacion),
            "url": f"/asociacion/{p.asociacion.email}",
            "imagen": p.imagen_url
        })

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
            "fecha": utc_to_colombia(v.fecha),
            "url": f"/catalogo?q={v.producto.nombre}",
            "imagen": v.producto.imagen_url
        })

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
            "fecha": utc_to_colombia(n.fecha_publicacion),
            "url": f"/noticias/{n.id}",
            "imagen": n.imagen_url
        })

    actividades.sort(key=lambda x: x["fecha"] if x["fecha"] else datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return actividades[:limite]