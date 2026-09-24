# -*- coding: utf-8 -*-
"""
Cliente de Conexión Directa a SharePoint / OneDrive (Microsoft Graph Cloud Reader).
Permite descargar y procesar en memoria archivos compartidos mediante su URL de SharePoint.
"""
import sys
import base64
import json
import subprocess
from pathlib import Path
import io
import pandas as pd
import requests

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import SILVER_DIR


class SharePointCloudClient:
    def __init__(self):
        self.silver_dir = SILVER_DIR

    def get_graph_token(self) -> str:
        """Obtiene el token de autenticación de Microsoft Graph usando Azure CLI corporativo."""
        try:
            res = subprocess.run(
                'az account get-access-token --resource-type ms-graph -o json',
                shell=True, capture_output=True, text=True, check=True
            )
            data = json.loads(res.stdout)
            return data["accessToken"]
        except Exception as e:
            raise RuntimeError(f"No se pudo obtener el token corporativo de Microsoft Graph: {e}")

    @staticmethod
    def encode_sharing_url(sharing_url: str) -> str:
        """Codifica una URL compartida de SharePoint/OneDrive para la API de Microsoft Graph."""
        url_bytes = sharing_url.encode("utf-8")
        base64_bytes = base64.b64encode(url_bytes)
        encoded_url = base64_bytes.decode("utf-8").rstrip("=").replace("/", "_").replace("+", "-")
        return "u!" + encoded_url

    def fetch_excel_from_sharepoint_url(self, sharing_url: str) -> pd.ExcelFile:
        """
        Descarga el archivo Excel directamente desde la URL de SharePoint en memoria
        sin guardarlo en el disco duro.
        """
        token = self.get_graph_token()
        encoded = self.encode_sharing_url(sharing_url)
        endpoint = f"https://graph.microsoft.com/v1.0/shares/{encoded}/driveItem/content"

        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(endpoint, headers=headers)
        
        if resp.status_code == 200:
            return pd.ExcelFile(io.BytesIO(resp.content))
        elif resp.status_code == 302:
            # Redirección de descarga directa
            download_url = resp.headers.get("Location")
            direct_resp = requests.get(download_url)
            return pd.ExcelFile(io.BytesIO(direct_resp.content))
        else:
            raise ConnectionError(f"Error ({resp.status_code}) al consultar SharePoint: {resp.text}")


if __name__ == "__main__":
    print("Módulo de Conexión Directa a SharePoint / Microsoft 365 compilado y listo.")
