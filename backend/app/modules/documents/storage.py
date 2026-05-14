"""
Capa de almacenamiento: subida de documentos a Cloudinary.
"""
import io
from fastapi import UploadFile
from app.services.upload_service import upload_raw, upload_image
from app.cloudinary_utils import delete_cloudinary_asset

def guardar_documento(html_content: str, filename: str, folder: str = "documentos") -> str:
    """Sube el HTML como archivo raw a Cloudinary y retorna la URL."""
    file_bytes = io.BytesIO(html_content.encode("utf-8"))
    file = UploadFile(filename=filename, file=file_bytes, headers={"content-type": "text/html"})
    return upload_raw(file, folder=folder)

def eliminar_documento(url: str):
    """Elimina un documento de Cloudinary por su URL."""
    delete_cloudinary_asset(url)