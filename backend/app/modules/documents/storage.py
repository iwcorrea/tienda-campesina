"""Almacenamiento de documentos en Cloudinary."""
import cloudinary.uploader

def guardar_documento(contenido_html: str, filename: str, folder: str) -> str:
    """
    Sube un documento HTML a Cloudinary y retorna la URL.
    """
    result = cloudinary.uploader.upload(
        contenido_html.encode('utf-8'),
        resource_type="raw",
        folder=folder,
        public_id=filename.rsplit('.', 1)[0],
        format="html",
        use_filename=True,
        unique_filename=True,
    )
    return result.get("secure_url", "")