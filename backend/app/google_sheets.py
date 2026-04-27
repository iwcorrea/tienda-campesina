import os
import gspread
from google.oauth2.service_account import Credentials

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
    """Devuelve la hoja 'Productos' (pestaña 2). Si no existe, la crea con encabezados actualizados."""
    client = _get_client()
    SHEET_ID = os.getenv("SHEET_ID")
    if not SHEET_ID:
        raise RuntimeError("Falta la variable SHEET_ID.")
    spreadsheet = client.open_by_key(SHEET_ID)
    try:
        ws = spreadsheet.worksheet("Productos")
    except gspread.exceptions.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title="Productos", rows=1000, cols=10)
        ws.append_row(["id", "email", "nombre", "descripcion", "precio", "imagen_url", "fecha", "tipo", "tipo_precio"])
        return ws
    # Si ya existe pero le faltan columnas, actualizamos los encabezados
    headers = ws.row_values(1)
    if len(headers) < 9 or headers[0] != "id":
        ws.insert_row(["id", "email", "nombre", "descripcion", "precio", "imagen_url", "fecha", "tipo", "tipo_precio"], 1)
    return ws