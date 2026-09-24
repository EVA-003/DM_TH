# -*- coding: utf-8 -*-
"""
Pipeline de Ingesta Bronze: Descarga y almacenamiento de entidades crudas desde Buk.
"""
import sys
from pathlib import Path

# Asegurar que la raíz del proyecto esté en el sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import json
import logging
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd
from config.settings import BRONZE_DIR
from src.ingestion.buk_client import BukClient

logger = logging.getLogger("BronzePipeline")


class BronzePipeline:
    def __init__(self, client: BukClient = None):
        self.client = client or BukClient()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def _sanitize_for_parquet(self, data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Sanitiza estructuras anidadas o tipos mixtos para persistencia limpia en Parquet."""
        df = pd.DataFrame(data)
        for col in df.columns:
            # Si la columna contiene tipos complejos (dict, list), serializar a JSON string
            if df[col].apply(lambda x: isinstance(x, (dict, list))).any():
                df[col] = df[col].apply(lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (dict, list)) else (str(x) if pd.notnull(x) else None))
            elif df[col].dtype == "object":
                # Asegurar que columnas tipo object no tengan colisiones de tipos para PyArrow
                df[col] = df[col].apply(lambda x: str(x) if pd.notnull(x) else None)
        return df

    def _save_raw(self, entity_name: str, data: List[Dict[str, Any]]) -> Path:
        entity_dir = BRONZE_DIR / entity_name
        entity_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Guardar JSON crudo original (fidelidad 100% de la API)
        json_file = entity_dir / f"{entity_name}_{self.timestamp}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump({
                "entity": entity_name,
                "ingestion_timestamp": datetime.now().isoformat(),
                "record_count": len(data),
                "data": data
            }, f, ensure_ascii=False, indent=2)

        # 2. Guardar copia en Parquet para consultas de alta velocidad
        parquet_file = entity_dir / f"{entity_name}_latest.parquet"
        df = self._sanitize_for_parquet(data)
        df["_ingestion_timestamp"] = datetime.now()
        df.to_parquet(parquet_file, index=False, engine="pyarrow")

        logger.info(f"Guardado Bronze para [{entity_name}]: {len(data)} registros en {parquet_file.name}")
        return parquet_file

    def run_full_ingestion(self) -> Dict[str, int]:
        summary = {}
        
        # 1. Empresas
        companies = self.client.get_companies()
        self._save_raw("companies", companies)
        summary["companies"] = len(companies)

        # 2. Áreas
        areas = self.client.get_areas()
        self._save_raw("areas", areas)
        summary["areas"] = len(areas)

        # 3. Cargos / Roles
        roles = self.client.get_roles()
        self._save_raw("roles", roles)
        summary["roles"] = len(roles)

        # 4. Sedes / Localidades
        locations = self.client.get_locations()
        self._save_raw("locations", locations)
        summary["locations"] = len(locations)

        # 5. Períodos de Nómina
        periods = self.client.get_process_periods()
        self._save_raw("process_periods", periods)
        summary["process_periods"] = len(periods)

        # 6. Catálogo de Ítems / Conceptos
        items = self.client.get_items()
        self._save_raw("items", items)
        summary["items"] = len(items)

        # 7. Maestro Completo de Colaboradores
        employees = self.client.get_employees()
        self._save_raw("employees", employees)
        summary["employees"] = len(employees)

        # 8. Vacaciones Históricas y Actuales
        vacations = self.client.get_vacations()
        self._save_raw("vacations", vacations)
        summary["vacations"] = len(vacations)

        # 9. Ausencias / Licencias / Permisos
        absences = self.client.get_absences()
        self._save_raw("absences", absences)
        summary["absences"] = len(absences)

        # 10. Festivos Oficiales
        holidays = self.client.get_holidays()
        self._save_raw("holidays", holidays)
        summary["holidays"] = len(holidays)

        logger.info(f"Ingesta Bronze completada exitosamente: {summary}")
        return summary


if __name__ == "__main__":
    pipeline = BronzePipeline()
    pipeline.run_full_ingestion()
