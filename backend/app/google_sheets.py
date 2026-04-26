import os
import gspread
from google.oauth2.service_account import Credentials
from google.cloud import storage
import datetime

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def _get_credentials():
    creds_json = os.getenv("GOOGLE_CREDENTIALS")
    if creds_json:
        import json
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    else:
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not creds_path:
            raise RuntimeError("No se encontraron credenciales de Google.")
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    return creds

def _get_client():
    creds = _get_credentials()
    return gspread.authorize(creds)

def get_sheet():
    """Devuelve la hoja 1 (usuarios)."""
    client = _get_client()
    SHEET_ID = os.getenv("SHEET_ID")
    if not SHEET_ID:
        raise RuntimeError("Falta la variable SHEET_ID.")
    return client.open_by_key(SHEET_ID).sheet1

def get_products_sheet():
    """Devuelve la hoja 'Productos' (pestaña 2). Si no existe, la crea con encabezados."""
    client = _get_client()
    SHEET_ID = os.getenv("SHEET_ID")
    if not SHEET_ID:
        raise RuntimeError("Falta la variable SHEET_ID.")
    spreadsheet = client.open_by_key(SHEET_ID)
    try:
        return spreadsheet.worksheet("Productos")
    except gspread.exceptions.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title="Productos", rows=1000, cols=10)
        ws.append_row(["email", "nombre", "descripcion", "precio", "imagen_url", "fecha"])
        return ws

def upload_to_gcs(file_data, filename, folder=""):
    """Sube un archivo a Google Cloud Storage y retorna la URL pública."""
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    if not bucket_name:
        raise RuntimeError("Falta la variable GCS_BUCKET_NAME.")
    
    creds = _get_credentials()
    storage_client = storage.Client(credentials=creds)
    bucket = storage_client.bucket(bucket_name)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    blob_name = f"{folder}/{timestamp}_{filename}" if folder else f"{timestamp}_{filename}"
    blob = bucket.blob(blob_name)
    
    blob.upload_from_file(file_data.file, content_type=file_data.content_type)
    blob.make_public()
    return blob.public_url