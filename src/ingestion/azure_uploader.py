import os
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AzureUploader")

BASE_DIR = Path(__file__).resolve().parent.parent.parent

from config.settings import (
    AZURE_STORAGE_ACCOUNT,
    AZURE_STORAGE_CONNECTION_STRING,
    AZURE_CONTAINERS
)

STORAGE_ACCOUNT = AZURE_STORAGE_ACCOUNT
CONTAINERS = AZURE_CONTAINERS

def generate_azure_cli_commands():
    """Genera los comandos de Azure CLI listos para ejecutar en terminal."""
    cmd_bronze = f'az storage blob upload-batch --account-name {STORAGE_ACCOUNT} --destination {CONTAINERS["bronze"]} --destination-path talento_humano --source "{BASE_DIR / "data" / "bronze"}" --auth-mode key'
    cmd_silver = f'az storage blob upload-batch --account-name {STORAGE_ACCOUNT} --destination {CONTAINERS["silver"]} --destination-path talento_humano --source "{BASE_DIR / "data" / "silver"}" --auth-mode key'
    cmd_gold   = f'az storage blob upload-batch --account-name {STORAGE_ACCOUNT} --destination {CONTAINERS["gold"]} --destination-path talento_humano --source "{BASE_DIR / "data" / "gold"}" --auth-mode key'
    cmd_sql    = f'az storage blob upload-batch --account-name {STORAGE_ACCOUNT} --destination {CONTAINERS["gold"]} --destination-path talento_humano/sql --source "{BASE_DIR / "data" / "sql"}" --auth-mode key'

    return {
        "bronze": cmd_bronze,
        "silver": cmd_silver,
        "gold": cmd_gold,
        "sql": cmd_sql
    }

def upload_with_azure_sdk(connection_string: str = None):
    """Sube todos los datasets usando el SDK de Azure Blob Storage."""
    try:
        from azure.storage.blob import BlobServiceClient
        from azure.identity import AzureCliCredential, DefaultAzureCredential

        conn_str = connection_string or AZURE_STORAGE_CONNECTION_STRING
        if conn_str:
            client = BlobServiceClient.from_connection_string(conn_str)
        else:
            account_url = f"https://{STORAGE_ACCOUNT}.blob.core.windows.net"
            try:
                credential = AzureCliCredential()
                client = BlobServiceClient(account_url, credential=credential)
            except Exception:
                credential = DefaultAzureCredential()
                client = BlobServiceClient(account_url, credential=credential)

        layers = [
            (BASE_DIR / "data" / "bronze", CONTAINERS["bronze"]),
            (BASE_DIR / "data" / "silver", CONTAINERS["silver"]),
            (BASE_DIR / "data" / "gold", CONTAINERS["gold"]),
            (BASE_DIR / "data" / "sql", CONTAINERS["gold"])
        ]

        for local_dir, container_name in layers:
            if not local_dir.exists():
                continue
            container_client = client.get_container_client(container_name)
            logger.info(f"Subiendo archivos de {local_dir.name} a contenedor {container_name}/talento_humano/...")
            
            for file_path in local_dir.rglob("*"):
                if file_path.is_file():
                    rel_path = file_path.relative_to(local_dir)
                    blob_name = f"talento_humano/{local_dir.name}/{rel_path}".replace("\\", "/")
                    if local_dir.name in ["gold", "silver", "bronze"]:
                        blob_name = f"talento_humano/{rel_path}".replace("\\", "/")
                        
                    logger.info(f"  • Subiendo: {blob_name}")
                    with open(file_path, "rb") as data:
                        container_client.upload_blob(name=blob_name, data=data, overwrite=True)

        logger.info("🎉 Subida a Azure Blob Storage completada con éxito.")
        return True
    except Exception as e:
        logger.error(f"Error subiendo a Azure Blob: {e}")
        return False

if __name__ == "__main__":
    cmds = generate_azure_cli_commands()
    print("=== COMANDOS AZURE CLI PARA SUBIR A stmaajidwhdev ===")
    for k, v in cmds.items():
        print(f"\n[{k.upper()}]\n{v}")
