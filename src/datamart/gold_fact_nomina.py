# -*- coding: utf-8 -*-
"""
Capa Gold: Generación del Datamart Dimensional de Gestión de Nómina Mensual.
Integra colaboradores con la Sábana de Conceptos de Buk (Comisiones y Horas Extras).
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import logging
from datetime import datetime
import pandas as pd
import numpy as np

from config.settings import SILVER_DIR, GOLD_DIR
from config.mapping_rules import PORCENTAJES_PRESTACIONALES

logger = logging.getLogger("GoldDatamart")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class GoldNominaDatamart:
    def __init__(self):
        self.silver_dir = SILVER_DIR
        self.gold_dir = GOLD_DIR

    def generate_monthly_fact(self, year: int = 2026, month: int = 7, cutoff_date: str = None) -> pd.DataFrame:
        logger.info(f"Generando Datamart Gold para el período: {year}-{month:02d}...")
        
        silver_emp_path = self.silver_dir / "silver_employees.parquet"
        if not silver_emp_path.exists():
            from src.processing.silver_employees import SilverEmployeesProcessor
            SilverEmployeesProcessor().process()
        
        df_emp = pd.read_parquet(silver_emp_path)

        if not cutoff_date:
            import calendar
            _, last_day = calendar.monthrange(year, month)
            cutoff_date = f"{year}-{month:02d}-{last_day:02d}"

        cutoff_dt = pd.to_datetime(cutoff_date)
        start_month_dt = pd.to_datetime(f"{year}-{month:02d}-01")

        # Población activa en el mes
        df_emp["fecha_ingreso_dt"] = pd.to_datetime(df_emp["fecha_ingreso"], errors="coerce")
        df_emp["fecha_retiro_dt"] = pd.to_datetime(df_emp["fecha_retiro"], errors="coerce")

        cond_ingreso = df_emp["fecha_ingreso_dt"].isna() | (df_emp["fecha_ingreso_dt"] <= cutoff_dt)
        cond_retiro = df_emp["fecha_retiro_dt"].isna() | (df_emp["fecha_retiro_dt"] >= start_month_dt)

        df_activos = df_emp[cond_ingreso & cond_retiro].copy()
        df_activos = df_activos.drop_duplicates(subset=["documento"], keep="last")

        df_activos["periodo_anio"] = year
        df_activos["periodo_mes"] = month
        df_activos["periodo_corte"] = cutoff_date

        # Cruzar con Sábana de Conceptos si existe
        concepts_path = self.silver_dir / "silver_payroll_concepts.parquet"
        if concepts_path.exists():
            df_concepts = pd.read_parquet(concepts_path)
            df_activos = df_activos.merge(df_concepts, on="documento", how="left")
            df_activos["comisiones"] = df_activos["comisiones"].fillna(0.0)
            df_activos["horas_extras"] = df_activos["horas_extras"].fillna(0.0)
            df_activos["cantidad_horas_extras"] = df_activos["cantidad_horas_extras"].fillna(0.0)
            df_activos["auxilio_transporte"] = df_activos["auxilio_transporte"].fillna(0.0)
            df_activos["otros_devengados"] = df_activos["otros_devengados"].fillna(0.0)
        else:
            df_activos["comisiones"] = 0.0
            df_activos["horas_extras"] = 0.0
            df_activos["cantidad_horas_extras"] = 0.0
            df_activos["auxilio_transporte"] = 0.0
            df_activos["otros_devengados"] = 0.0

        # Totales devengados reales
        df_activos["total_devengado"] = (
            df_activos["salario_base"] +
            df_activos["comisiones"] +
            df_activos["horas_extras"] +
            df_activos["otros_devengados"]
        ).round(2)

        # Provisiones y Cargas Prestacionales de ley sobre devengado real
        df_activos["provision_cesantias"] = (df_activos["total_devengado"] * PORCENTAJES_PRESTACIONALES["cesantias"]).round(2)
        df_activos["provision_intereses_cesantias"] = (df_activos["total_devengado"] * PORCENTAJES_PRESTACIONALES["intereses_cesantias"]).round(2)
        df_activos["provision_prima"] = (df_activos["total_devengado"] * PORCENTAJES_PRESTACIONALES["prima_servicios"]).round(2)
        df_activos["provision_vacaciones"] = (df_activos["salario_base"] * PORCENTAJES_PRESTACIONALES["vacaciones"]).round(2)
        df_activos["seguridad_social_pension"] = (df_activos["total_devengado"] * PORCENTAJES_PRESTACIONALES["pension_empleador"]).round(2)
        df_activos["parafiscales_caja"] = (df_activos["total_devengado"] * PORCENTAJES_PRESTACIONALES["caja_compensacion"]).round(2)
        df_activos["seguridad_social_arl"] = (df_activos["total_devengado"] * df_activos["tarifa_arl_pct"]).round(2)

        df_activos["total_carga_prestacional"] = (
            df_activos["provision_cesantias"] +
            df_activos["provision_intereses_cesantias"] +
            df_activos["provision_prima"] +
            df_activos["provision_vacaciones"] +
            df_activos["seguridad_social_pension"] +
            df_activos["parafiscales_caja"] +
            df_activos["seguridad_social_arl"]
        ).round(2)

        df_activos["costo_total_empleador"] = (df_activos["total_devengado"] + df_activos["total_carga_prestacional"]).round(2)

        output_gold = self.gold_dir / f"fact_nomina_{year}_{month:02d}.parquet"
        df_activos.to_parquet(output_gold, index=False)
        logger.info(f"Datamart Gold generado: {len(df_activos)} colaboradores activos en {output_gold.name}")
        return df_activos


if __name__ == "__main__":
    datamart = GoldNominaDatamart()
    df_gold = datamart.generate_monthly_fact(2026, 7)
    from src.exports.report_generator import NominaReportGenerator
    NominaReportGenerator().generate_excel_report(2026, 7)
    print("\n--- RESUMEN DATAMART GOLD CON SÁBANA DE CONCEPTOS (JULIO 2026) ---")
    print(f"Colaboradores Activos  : {len(df_gold)}")
    print(f"Masa Salarial Base     : ${df_gold['salario_base'].sum():,.2f} COP")
    print(f"Comisiones Liquidadas  : ${df_gold['comisiones'].sum():,.2f} COP")
    print(f"Horas Extras Liquidadas: ${df_gold['horas_extras'].sum():,.2f} COP")
    print(f"Total Devengado Real   : ${df_gold['total_devengado'].sum():,.2f} COP")
    print(f"Costo Total Compañía   : ${df_gold['costo_total_empleador'].sum():,.2f} COP")
