import io
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile, status
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload

# Scope mínimo para crear/leer/editar archivos creados por la app.
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

# Ruta al archivo de credenciales del Service Account.
BASE_DIR = Path(__file__).resolve().parents[2]
CREDENTIALS_PATH = BASE_DIR / "google_drive" / "credentials.json"

# Permitir sobreescribir la ruta con variable de entorno (útil en producción)
ENV_CREDENTIALS_PATH = os.getenv("GOOGLE_DRIVE_CREDENTIALS_PATH")
FINAL_CREDENTIALS_PATH = (
    Path(ENV_CREDENTIALS_PATH)
    if ENV_CREDENTIALS_PATH and Path(ENV_CREDENTIALS_PATH).exists()
    else CREDENTIALS_PATH
)


@lru_cache(maxsize=1)
def get_drive_service():
    """
    Carga credenciales y construye el cliente de Google Drive.
    El resultado se cachea para no leer el archivo JSON en cada llamada.
    """
    try:
        if not FINAL_CREDENTIALS_PATH.exists():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"No existe el archivo de credenciales en {FINAL_CREDENTIALS_PATH}",
            )

        credentials = service_account.Credentials.from_service_account_file(
            str(FINAL_CREDENTIALS_PATH),
            scopes=SCOPES,
        )
        return build("drive", "v3", credentials=credentials)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cargar servicio de Google Drive: {exc}",
        ) from exc


# Función de compatibilidad (si hay código que aún llame a load_drive_service)
def load_drive_service():
    return get_drive_service()


def crear_carpeta_si_no_existe(nombre_carpeta: str, parent_id: Optional[str] = None) -> str:
    """
    Busca una carpeta por nombre en el nivel indicado.
    Si no existe, la crea y retorna su ID.
    """
    service = get_drive_service()

    try:
        # Sanitizar nombre para la query (escapar comillas simples)
        nombre_sanitizado = nombre_carpeta.replace("'", "\\'")
        query_parts = [
            "mimeType='application/vnd.google-apps.folder'",
            f"name='{nombre_sanitizado}'",
            "trashed=false",
        ]
        if parent_id:
            query_parts.append(f"'{parent_id}' in parents")

        query = " and ".join(query_parts)
        resultado = (
            service.files()
            .list(q=query, spaces="drive", fields="files(id, name)", pageSize=1)
            .execute()
        )

        carpetas = resultado.get("files", [])
        if carpetas:
            return carpetas[0]["id"]

        # No existe, la creamos
        metadata = {
            "name": nombre_carpeta,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_id:
            metadata["parents"] = [parent_id]

        carpeta = service.files().create(body=metadata, fields="id").execute()
        return carpeta["id"]
    except HttpError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error de Google Drive al buscar/crear carpeta: {exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al crear carpeta en Drive: {exc}",
        ) from exc


async def subir_archivo(
    archivo: UploadFile, carpeta_id: str, nombre_archivo: Optional[str] = None
) -> str:
    """
    Sube un archivo a Google Drive usando MediaIoBaseUpload y retorna el file_id.
    """
    service = get_drive_service()

    try:
        contenido = await archivo.read()
        if not contenido:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo está vacío.",
            )

        file_stream = io.BytesIO(contenido)
        media = MediaIoBaseUpload(
            file_stream,
            mimetype=archivo.content_type or "application/octet-stream",
            resumable=True,
        )

        metadata = {
            "name": nombre_archivo or archivo.filename or "archivo_sin_nombre",
            "parents": [carpeta_id],
        }

        creado = service.files().create(body=metadata, media_body=media, fields="id").execute()
        return creado["id"]
    except HTTPException:
        raise
    except HttpError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error de Google Drive al subir archivo: {exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al subir archivo a Drive: {exc}",
        ) from exc
    finally:
        await archivo.close()


def eliminar_archivo(file_id: str):
    """Elimina un archivo de Google Drive por su ID."""
    service = get_drive_service()
    try:
        service.files().delete(fileId=file_id).execute()
    except HttpError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error de Google Drive al eliminar archivo: {exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al eliminar archivo de Drive: {exc}",
        ) from exc


def hacer_publico(file_id: str):
    """
    Asigna permiso público de lectura (anyone/reader).
    Si el permiso ya existe (error 403), lo ignora silenciosamente.
    """
    service = get_drive_service()
    try:
        permiso = {"type": "anyone", "role": "reader"}
        service.permissions().create(fileId=file_id, body=permiso).execute()
    except HttpError as exc:
        # El error 403 significa que el permiso ya existe (o no se puede crear)
        # En ese caso, simplemente ignoramos y continuamos.
        if exc.resp.status == 403:
            return
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error de Google Drive al cambiar permisos: {exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al hacer público el archivo: {exc}",
        ) from exc


def obtener_url_imagen(file_id: str) -> str:
    """
    Retorna el webViewLink del archivo (vista previa en navegador).
    Si el archivo no es público, intenta hacerlo público una sola vez.
    """
    service = get_drive_service()
    try:
        # Primero intentamos obtener el enlace sin modificar permisos
        archivo = service.files().get(fileId=file_id, fields="webViewLink").execute()
        url = archivo.get("webViewLink")
        if url:
            return url
    except HttpError as exc:
        # Si el error es 403 (permiso denegado), significa que no es público
        if exc.resp.status == 403:
            # Hacer público por primera vez
            hacer_publico(file_id)
            # Volvemos a obtener el enlace
            archivo = service.files().get(fileId=file_id, fields="webViewLink").execute()
            url = archivo.get("webViewLink")
            if url:
                return url
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error de Google Drive al obtener URL de imagen: {exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al obtener URL de imagen: {exc}",
        ) from exc

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No se pudo obtener webViewLink del archivo.",
    )


def obtener_url_directa(file_id: str) -> str:
    """
    Genera una URL de descarga directa para incrustar imágenes en etiquetas <img>.
    Requiere que el archivo sea público (lo hace automáticamente si no lo es).
    """
    hacer_publico(file_id)  # Asegura que sea público
    # Formato de URL directa de Google Drive (útil para <img src="...">)
    return f"https://drive.google.com/uc?export=view&id={file_id}"