# -*- coding: utf-8 -*-
"""
Servicio de Datos en Nube (Azure Data Lake Storage Gen2).
Permite a la aplicación Maaji Talent consumir datasets directamente desde Azure
(bronze-zone, silver-zone y gold-zone en stmaajidwhdev) sin depender de archivos locales.
"""
import io
import json
import logging
from typing import Optional, Dict, Any, List
import pandas as pd
from azure.storage.blob import BlobServiceClient

from config.settings import (
    AZURE_STORAGE_ACCOUNT,
    AZURE_STORAGE_CONNECTION_STRING,
    AZURE_CONTAINERS,
    USE_AZURE_STORAGE
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AzureDataService")


class AzureDataService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(AzureDataService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, connection_string: Optional[str] = None):
        if self._initialized:
            return
        self.conn_str = connection_string or AZURE_STORAGE_CONNECTION_STRING
        self.containers = AZURE_CONTAINERS
        self.use_azure = USE_AZURE_STORAGE
        self._cache = {}

        if self.use_azure and self.conn_str:
            try:
                self.client = BlobServiceClient.from_connection_string(self.conn_str)
                logger.info(f"AzureDataService conectado exitosamente a '{AZURE_STORAGE_ACCOUNT}'.")
            except Exception as e:
                logger.error(f"Error conectando a Azure Blob Storage: {e}")
                self.client = None
        else:
            self.client = None
            logger.warning("AzureDataService no configurado con connection_string. Modo local activado.")

        self._initialized = True

    def is_connected(self) -> bool:
        return self.client is not None

    def _read_parquet_blob(self, container_key: str, blob_rel_path: str) -> Optional[pd.DataFrame]:
        cache_key = f"{container_key}:{blob_rel_path}"
        if cache_key in self._cache:
            return self._cache[cache_key].copy()

        if not self.is_connected():
            return None

        try:
            container_name = self.containers.get(container_key, f"{container_key}-zone")
            container_client = self.client.get_container_client(container_name)
            blob_name = f"talento_humano/{blob_rel_path}".replace("\\", "/")
            blob_client = container_client.get_blob_client(blob_name)

            if not blob_client.exists():
                logger.warning(f"Blob no encontrado en Azure: {container_name}/{blob_name}")
                return None

            download_stream = blob_client.download_blob()
            stream_bytes = io.BytesIO(download_stream.readall())
            df = pd.read_parquet(stream_bytes)
            self._cache[cache_key] = df
            logger.info(f"[Azure Cloud] Cargado Parquet desde {container_name}/{blob_name}: {len(df)} filas.")
            return df.copy()
        except Exception as e:
            logger.error(f"Error leyendo Parquet desde Azure ({blob_rel_path}): {e}")
            return None

    def _write_parquet_blob(self, container_key: str, blob_rel_path: str, df: pd.DataFrame) -> bool:
        if not self.is_connected():
            return False
        try:
            container_name = self.containers.get(container_key, f"{container_key}-zone")
            container_client = self.client.get_container_client(container_name)
            blob_name = f"talento_humano/{blob_rel_path}".replace("\\", "/")
            blob_client = container_client.get_blob_client(blob_name)

            out_stream = io.BytesIO()
            df.to_parquet(out_stream, index=False)
            out_stream.seek(0)
            blob_client.upload_blob(out_stream.getvalue(), overwrite=True)

            cache_key = f"{container_key}:{blob_rel_path}"
            self._cache[cache_key] = df.copy()
            logger.info(f"[Azure Cloud] Guardado Parquet en {container_name}/{blob_name}: {len(df)} filas.")
            return True
        except Exception as e:
            logger.error(f"Error escribiendo Parquet a Azure ({blob_rel_path}): {e}")
            return False

    def _read_json_blob(self, container_key: str, blob_rel_path: str) -> Optional[Any]:
        if not self.is_connected():
            return None
        try:
            container_name = self.containers.get(container_key, f"{container_key}-zone")
            container_client = self.client.get_container_client(container_name)
            blob_name = f"talento_humano/{blob_rel_path}".replace("\\", "/")
            blob_client = container_client.get_blob_client(blob_name)

            if not blob_client.exists():
                return None

            data_str = blob_client.download_blob().readall().decode("utf-8")
            return json.loads(data_str)
        except Exception as e:
            logger.error(f"Error leyendo JSON desde Azure ({blob_rel_path}): {e}")
            return None

    def _write_json_blob(self, container_key: str, blob_rel_path: str, data: Any) -> bool:
        if not self.is_connected():
            return False
        try:
            container_name = self.containers.get(container_key, f"{container_key}-zone")
            container_client = self.client.get_container_client(container_name)
            blob_name = f"talento_humano/{blob_rel_path}".replace("\\", "/")
            blob_client = container_client.get_blob_client(blob_name)

            json_bytes = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
            blob_client.upload_blob(json_bytes, overwrite=True)
            return True
        except Exception as e:
            logger.error(f"Error escribiendo JSON a Azure ({blob_rel_path}): {e}")
            return False

    def get_gold_nomina(self, year: int = 2026, month: int = 7) -> Optional[pd.DataFrame]:
        blob_path = f"fact_nomina_{year}_{month:02d}.parquet"
        return self._read_parquet_blob("gold", blob_path)

    def save_gold_nomina(self, df: pd.DataFrame, year: int = 2026, month: int = 7) -> bool:
        blob_path = f"fact_nomina_{year}_{month:02d}.parquet"
        return self._write_parquet_blob("gold", blob_path, df)

    def get_silver_employees(self) -> Optional[pd.DataFrame]:
        return self._read_parquet_blob("silver", "silver_employees.parquet")

    def get_silver_vacations(self) -> Optional[pd.DataFrame]:
        return self._read_parquet_blob("silver", "silver_vacations_by_leader.parquet")

    def get_silver_temporales(self) -> Optional[pd.DataFrame]:
        return self._read_parquet_blob("silver", "silver_temporales.parquet")

    def get_vacation_requests(self) -> List[Dict[str, Any]]:
        res = self._read_json_blob("silver", "vacation_requests.json")
        return res if isinstance(res, list) else []

    def save_vacation_requests(self, requests_data: List[Dict[str, Any]]) -> bool:
        return self._write_json_blob("silver", "vacation_requests.json", requests_data)

    def get_adjustments_workflow(self) -> List[Dict[str, Any]]:
        res = self._read_json_blob("silver", "adjustments_workflow.json")
        return res if isinstance(res, list) else []

    def save_adjustments_workflow(self, workflow_data: List[Dict[str, Any]]) -> bool:
        return self._write_json_blob("silver", "adjustments_workflow.json", workflow_data)

    def clear_cache(self):
        self._cache.clear()
        logger.info("Caché en memoria de AzureDataService invalidada.")


azure_data_service = AzureDataService()
