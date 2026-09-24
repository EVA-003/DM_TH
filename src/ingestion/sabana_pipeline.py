# -*- coding: utf-8 -*-
"""
Pipeline de Ingesta y Agrupación de la Sábana de Conceptos de Buk.
Extrae Comisiones, Horas Extras, Recargos y Auxilios agrupados por Cédula.
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

logger = logging.getLogger("SabanaPipeline")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class SabanaPipeline:
    def __init__(self):
        self.silver_dir = SILVER_DIR

    def process_file(self, file_path: str or Path) -> pd.DataFrame:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"No se encontró el archivo de sábana en: {path}")

        logger.info(f"Procesando Sábana de Conceptos de Buk desde: {path.name}...")
        
        # Leer archivo omitiendo las primeras 4 filas de metadata
        df = pd.read_excel(path, skiprows=4)
        
        # Normalizar nombres de columnas
        df.columns = [str(c).strip() for c in df.columns]
        
        # Identificar columnas clave
        col_doc = next((c for c in df.columns if "Documento" in c and "Tipo" not in c and "Cuenta" not in c), "Número de Documento")
        col_concepto = "Concepto"
        col_valor = "Suma de Valor"
        col_horas = "Cantidad Horas"

        # Limpiar documento
        df["documento"] = df[col_doc].astype(str).str.replace(".", "").str.replace(" ", "").str.strip()
        df["valor"] = pd.to_numeric(df[col_valor], errors="coerce").fillna(0.0)
        df["horas"] = pd.to_numeric(df[col_horas], errors="coerce").fillna(0.0)
        df["concepto_lower"] = df[col_concepto].astype(str).str.lower()

        # Categorizar conceptos
        def categorizar(c):
            if "comisi" in c:
                return "comision"
            elif any(k in c for k in ["hora extra", "recargo", "ajuste hora extra"]):
                return "hora_extra"
            elif "auxilio de transporte" in c and "extralegal" not in c:
                return "auxilio_transporte"
            elif any(k in c for k in ["bono", "auxilio de rodamiento", "extralegal", "sostenimiento"]):
                return "otros_devengados"
            return "otros"

        df["categoria"] = df["concepto_lower"].apply(categorizar)

        # Agrupar por documento y categoría
        df_devengados = df[df["categoria"] != "otros"].copy()
        
        resumen_list = []
        for doc, group in df_devengados.groupby("documento"):
            comisiones = group[group["categoria"] == "comision"]["valor"].sum()
            horas_extras = group[group["categoria"] == "hora_extra"]["valor"].sum()
            aux_transporte = group[group["categoria"] == "auxilio_transporte"]["valor"].sum()
            otros = group[group["categoria"] == "otros_devengados"]["valor"].sum()
            cant_he_horas = group[group["categoria"] == "hora_extra"]["horas"].sum()

            resumen_list.append({
                "documento": doc,
                "comisiones": round(float(comisiones), 2),
                "horas_extras": round(float(horas_extras), 2),
                "cantidad_horas_extras": round(float(cant_he_horas), 2),
                "auxilio_transporte": round(float(aux_transporte), 2),
                "otros_devengados": round(float(otros), 2)
            })

        df_resumen = pd.DataFrame(resumen_list)
        out_parquet = self.silver_dir / "silver_payroll_concepts.parquet"
        df_resumen.to_parquet(out_parquet, index=False)
        
        logger.info(f"Sábana procesada: {len(df_resumen)} colaboradores con conceptos liquidados guardados en {out_parquet.name}")
        logger.info(f"Total Comisiones: ${df_resumen['comisiones'].sum():,.2f} COP")
        logger.info(f"Total Horas Extras: ${df_resumen['horas_extras'].sum():,.2f} COP (Total Horas: {df_resumen['cantidad_horas_extras'].sum():,.1f}h)")
        
        return df_resumen


if __name__ == "__main__":
    test_path = r"c:\Users\oberrio\Downloads\SABANA DE CONCEPTOS JULIO DE 2025.xlsx"
    p = SabanaPipeline()
    df_c = p.process_file(test_path)
    print("\n--- MUESTRA CONCEPTOS LIQUIDADOS POR COLABORADOR ---")
    print(df_c[df_c["comisiones"] > 0].head(8).to_string())
