from fastapi import UploadFile
import cloudinary.uploader


def upload_image(file: UploadFile, folder: str = "general") -> str:
    """Sube una imagen a Cloudinary y devuelve la URL segura."""
    if not file or not file.filename:
        return ""
    try:
        result = cloudinary.uploader.upload(
            file.file,
            folder=folder,
            filename=file.filename,
            use_filename=True,
            unique_filename=True,
            access_mode="public",
        )
        return result.get("secure_url", "")
    except Exception:
        return ""


def upload_raw(file: UploadFile, folder: str = "documentos") -> str:
    """Sube un archivo raw (PDF, etc.) a Cloudinary y devuelve la URL segura."""
    if not file or not file.filename:
        return ""
    try:
        result = cloudinary.uploader.upload(
            file.file,
            folder=folder,
            resource_type="raw",
            filename=file.filename,
            use_filename=True,
            unique_filename=True,
            access_mode="public",
        )
        return result.get("secure_url", "")
    except Exception:
        return ""