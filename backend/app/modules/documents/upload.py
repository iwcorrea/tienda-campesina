import cloudinary.uploader

def upload_raw(file, folder: str, filename: str = "") -> str:
    """Sube un archivo a Cloudinary y retorna la URL."""
    result = cloudinary.uploader.upload(
        file,
        folder=folder,
        filename=filename,
        use_filename=True,
        unique_filename=True,
        access_mode="public"
    )
    return result.get("secure_url", "")

def upload_image(file, folder: str, filename: str = "") -> str:
    """Sube una imagen a Cloudinary y retorna la URL."""
    return upload_raw(file, folder, filename)