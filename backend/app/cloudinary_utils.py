import os
import cloudinary

cloudinary.config(cloudinary_url=os.getenv("CLOUDINARY_URL"))


def delete_cloudinary_asset(url: str, resource_type: str = "image"):
    """Elimina un recurso de Cloudinary dado su URL pública."""
    if not url or "cloudinary.com" not in url:
        return
    try:
        parts = url.split("/")
        upload_idx = -1
        for i, part in enumerate(parts):
            if part == "upload":
                upload_idx = i
                break
        if upload_idx == -1 or upload_idx + 2 >= len(parts):
            return
        public_id_with_ext = "/".join(parts[upload_idx + 2:])
        if resource_type in ("image", "video"):
            public_id = public_id_with_ext.rsplit(".", 1)[0]
        else:
            public_id = public_id_with_ext
        cloudinary.uploader.destroy(public_id, resource_type=resource_type)
    except Exception:
        pass