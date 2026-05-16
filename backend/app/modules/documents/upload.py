import cloudinary.uploader

def upload_raw(file, folder: str, filename: str = "") -> str:
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
    return upload_raw(file, folder, filename)