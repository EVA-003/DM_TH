# -*- coding: utf-8 -*-
"""
Pipeline de Ingesta y Normalización de Personal Temporal (Mas SAS y Art Mode SAS).
Procesa la "Maestra de Personal Temporal" de la carpeta de Compensación.
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import logging
import pandas as pd
import numpy as np
from config.settings import SILVER_DIR, OUTPUTS_DIR
from config.mapping_rules import TARIFAS_ARL, clasificar_mod_moi

logger = logging.getLogger("TemporalesPipeline")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class TemporalesPipeline:
    def __init__(self):
        self.silver_dir = SILVER_DIR

    def process_file(self, file_path: str or Path) -> pd.DataFrame:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"No se encontró el archivo de temporales en: {path}")

        logger.info(f"Procesando Maestra de Personal Temporal desde: {path.name}...")
        
        xls = pd.ExcelFile(path)
        all_records = []

        # Hojas esperadas: "Libro 1 Temporal MAS SAS", "Libro 2 Temporal ART MODE" o nombres similares
        for sheet_name in xls.sheet_names:
            sheet_lower = sheet_name.lower()
            empresa_default = "MAS S.A.S BIC" if "mas" in sheet_lower else ("ART MODE S.A.S BIC" if "art" in sheet_lower or "armo" in sheet_lower else "Temporal General")
            
            df_sheet = pd.read_excel(xls, sheet_name=sheet_name)
            df_sheet.columns = [str(c).strip().lower().replace(" ", "_") for c in df_sheet.columns]
            
            # Buscar columnas estándar
            col_doc = next((c for c in df_sheet.columns if "cedula" in c or "documento" in c or "numero" in c), None)
            col_nom = next((c for c in df_sheet.columns if "nombre" in c or "empleado" in c or "trabajador" in c), None)
            col_car = next((c for c in df_sheet.columns if "cargo" in c or "oficio" in c), None)
            col_sal = next((c for c in df_sheet.columns if "salario" in c or "sueldo" in c or "basico" in c), None)
            col_ing = next((c for c in df_sheet.columns if "ingreso" in c or "inicio" in c or "fecha" in c), None)
            col_ret = next((c for c in df_sheet.columns if "retiro" in c or "fin" in c or "egreso" in c), None)
            col_arl = next((c for c in df_sheet.columns if "arl" in c or "riesgo" in c), None)
            col_sed = next((c for c in df_sheet.columns if "sede" in c or "ubicacion" in c or "tienda" in c), None)

            if not col_doc or not col_nom:
                continue

            for _, row in df_sheet.iterrows():
                doc_raw = str(row.get(col_doc) or "").replace(".", "").replace(" ", "").strip()
                if not doc_raw or doc_raw.lower() in ["nan", "none", ""]:
                    continue

                nombre_raw = str(row.get(col_nom) or "").strip()
                cargo_raw = str(row.get(col_car) or "Operario Temporal").strip() if col_car else "Operario Temporal"
                salario_raw = float(row.get(col_sal) or 1300000.0) if col_sal else 1300000.0
                
                fecha_ing_raw = str(row.get(col_ing) or "")[:10] if col_ing else None
                fecha_ret_raw = str(row.get(col_ret) or "")[:10] if col_ret else None
                
                risk_type = str(row.get(col_arl) or "minimo").lower() if col_arl else "minimo"
                tarifa_arl = TARIFAS_ARL.get(risk_type, 0.00522)
                
                sede_raw = str(row.get(col_sed) or "Planta Principal") if col_sed else "Planta Principal"
                clasificacion_mo = clasificar_mod_moi(cargo_raw, "", "")

                all_records.append({
                    "colaborador_id": f"TEMP_{doc_raw}",
                    "tipo_documento": "CC",
                    "documento": doc_raw,
                    "nombre_completo": nombre_raw,
                    "empresa_nombre": empresa_default,
                    "area_nombre": "Operaciones Temporales",
                    "cargo_nombre": cargo_raw,
                    "centro_costos": "TEMPORAL",
                    "sede": sede_raw,
                    "tipo_contrato": "Obra y Labor (Temporal)",
                    "fecha_ingreso": fecha_ing_raw,
                    "fecha_retiro": fecha_ret_raw,
                    "antiguedad_meses": 1.0,
                    "salario_base": salario_raw,
                    "tipo_riesgo_arl": risk_type,
                    "tarifa_arl_pct": tarifa_arl,
                    "clasificacion_mano_obra": clasificacion_mo,
                    "es_temporal": True
                })

        df_temporales = pd.DataFrame(all_records)
        out_parquet = self.silver_dir / "silver_temporales.parquet"
        df_temporales.to_parquet(out_parquet, index=False)
        logger.info(f"Capa Silver Temporales guardada: {len(df_temporales)} registros en {out_parquet.name}")
        return df_temporales


if __name__ == "__main__":
    print("Módulo de Ingesta de Temporales compilado y listo para recibir archivos de Compensación.")
