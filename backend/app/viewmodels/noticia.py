from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class NoticiaViewModel:
    id: str
    titulo: str
    contenido: str
    imagen_url: Optional[str]
    fecha_publicacion: datetime

    @classmethod
    def from_orm(cls, noticia) -> "NoticiaViewModel":
        return cls(
            id=noticia.id,
            titulo=noticia.titulo,
            contenido=noticia.contenido,
            imagen_url=noticia.imagen_url,
            fecha_publicacion=noticia.fecha_publicacion,
        )