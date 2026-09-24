# -*- coding: utf-8 -*-
"""
Configuración central del proyecto Datamart de Nómina (Maaji - Buk Colombia).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Directorio raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables de entorno desde .env
load_dotenv(BASE_DIR / ".env")

# Rutas de almacenamiento de datos locales (fallback o caché)
DATA_DIR = BASE_DIR / "data"
BRONZE_DIR = DATA_DIR / "bronze"
SILVER_DIR = DATA_DIR / "silver"
GOLD_DIR = DATA_DIR / "gold"
OUTPUTS_DIR = DATA_DIR / "outputs"

for path in [DATA_DIR, BRONZE_DIR, SILVER_DIR, GOLD_DIR, OUTPUTS_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# Parámetros Buk API
BUK_API_TOKEN = os.getenv("BUK_API_TOKEN", "EMVvA6ppoVTtRdoXgqu8JSWj")
BUK_TENANT = os.getenv("BUK_TENANT", "maaji")
BUK_BASE_URL = os.getenv("BUK_BASE_URL", f"https://{BUK_TENANT}.buk.co/api/v1/colombia")

# Parámetros Azure Data Lake Storage Gen2 (stmaajidwhdev)
AZURE_STORAGE_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT", "stmaajidwhdev")
AZURE_STORAGE_KEY = os.getenv("AZURE_STORAGE_KEY", "")
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
USE_AZURE_STORAGE = os.getenv("USE_AZURE_STORAGE", "true").lower() in ("true", "1", "yes")
AZURE_CONTAINERS = {
    "bronze": "bronze-zone",
    "silver": "silver-zone",
    "gold": "gold-zone"
}

# Timeouts y Reintentos
REQUEST_TIMEOUT = 20
MAX_RETRIES = 3
PAGE_SIZE = 100
