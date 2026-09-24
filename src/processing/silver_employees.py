# -*- coding: utf-8 -*-
"""
Capa Silver: Normalización y Enriquecimiento Maestro de Colaboradores.
Integra ficha laboral, salarios vigentes, riesgo ARL, clasificación MOD/MOI y Foto oficial Buk.
"""
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import logging
from datetime import datetime
import pandas as pd
import numpy as np

from config.settings import BRONZE_DIR, SILVER_DIR
from config.mapping_rules import TARIFAS_ARL, clasificar_mod_moi

logger = logging.getLogger("SilverEmployees")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def calcular_antiguedad_interna(fecha_inicio_str: str, fecha_corte_str: str = "2026-07-31") -> dict:
    if not fecha_inicio_str or str(fecha_inicio_str).lower() in ["none", "nan", "nat", ""]:
        return {"dias": 0, "meses": 0.0, "anios": 0.0}
    try:
        f_ini = pd.to_datetime(str(fecha_inicio_str)[:10])
        f_corte = pd.to_datetime(str(fecha_corte_str)[:10])
        dias = max(0, (f_corte - f_ini).days)
        meses = round(dias / 30.4375, 1)
        anios = round(dias / 365.25, 1)
        return {"dias": dias, "meses": meses, "anios": anios}
    except Exception:
        return {"dias": 0, "meses": 0.0, "anios": 0.0}


class SilverEmployeesProcessor:
    def __init__(self):
        self.bronze_dir = BRONZE_DIR
        self.silver_dir = SILVER_DIR

    def _load_bronze(self, entity_name: str) -> pd.DataFrame:
        entity_path = self.bronze_dir / entity_name
        parquet_files = list(entity_path.glob("*.parquet"))
        if parquet_files:
            return pd.read_parquet(parquet_files[0])
        json_files = list(entity_path.glob("*.json"))
        if json_files:
            return pd.read_json(json_files[0])
        raise FileNotFoundError(f"No se encontró dataset Bronze para la entidad: {entity_name}")

    def process(self, reference_date: str = "2026-07-31") -> pd.DataFrame:
        logger.info("Iniciando procesamiento de Silver Employees...")
        
        df_employees = self._load_bronze("employees")
        df_companies = self._load_bronze("companies")
        df_areas = self._load_bronze("areas")
        df_roles = self._load_bronze("roles")
        df_locations = self._load_bronze("locations")

        # Extended Colombian branch and municipal locations in Buk
        buk_extended_locations = {
            495: "Medellín (Sede Principal)",
            509: "Rionegro / Oriente",
            440: "Bello",
            484: "Envigado",
            472: "Caldas (Antioquia)",
            467: "Copacabana",
            511: "Sabaneta",
            514: "Itagüí",
            928: "Bogotá D.C. (Retail / Tiendas)",
            1515: "Cali (Valle del Cauca)",
            592: "Cartagena (Bolívar)",
            558: "Barranquilla (Atlántico)",
            582: "Santa Marta (Magdalena)",
            630: "Bucaramanga (Santander)",
            754: "Manizales (Caldas)",
            819: "Popayán (Cauca)",
            1457: "Valle del Cauca",
            424: "Antioquia",
            919: "Cundinamarca"
        }

        companies_map = dict(zip(df_companies["id"], df_companies["name"]))
        areas_map = dict(zip(df_areas["id"], df_areas["name"]))
        roles_map = dict(zip(df_roles["id"], df_roles["name"]))
        locations_map = {**buk_extended_locations, **dict(zip(df_locations["id"], df_locations["name"]))}

        processed_rows = []
        for _, emp in df_employees.iterrows():
            current_job = emp.get("current_job") or {}
            if isinstance(current_job, str):
                try:
                    current_job = json.loads(current_job)
                except Exception:
                    current_job = {}
            elif not isinstance(current_job, dict):
                current_job = {}
            
            doc_type = emp.get("document_type") or "CC"
            doc_num = str(emp.get("document_number") or "").replace(".", "").replace(" ", "").strip()
            first_name = (emp.get("first_name") or "").strip()
            surname = (emp.get("surname") or "").strip()
            second_surname = (emp.get("second_surname") or "").strip()
            full_name = f"{first_name} {surname} {second_surname}".strip() or (emp.get("full_name") or "").strip()

            picture_url = emp.get("picture_url") or ""
            gender = emp.get("gender") or "F"

            company_id = current_job.get("company_id")
            area_id = current_job.get("area_id")
            role_id = current_job.get("role_id")
            location_id = current_job.get("location_id") or emp.get("location_id")

            company_name = companies_map.get(company_id, "MAS S.A.S BIC")
            area_name = areas_map.get(area_id, "General")
            role_name = roles_map.get(role_id, "Colaborador")
            location_name = locations_map.get(location_id, "Sede Principal")

            salario_base = float(current_job.get("wage") or current_job.get("base_wage") or 0.0)
            fecha_ingreso = emp.get("active_since") or current_job.get("start_date")
            fecha_retiro = emp.get("active_until") or current_job.get("end_date")
            contract_type = current_job.get("contract_type") or "Indefinido"

            antiguedad = calcular_antiguedad_interna(str(fecha_ingreso), reference_date)
            clasif_mo = clasificar_mod_moi(role_name, area_name, location_name)

            if any(k in role_name.lower() for k in ["confecci", "corte", "mecanic", "taller", "operari", "planta"]):
                risk_type = "medio"
            elif any(k in role_name.lower() for k in ["bodega", "logistica", "almacen", "despacho"]):
                risk_type = "bajo"
            else:
                risk_type = "minimo"

            tarifa_arl = TARIFAS_ARL.get(risk_type, 0.00522)
            valor_arl_estimado = round(salario_base * tarifa_arl, 2)

            processed_rows.append({
                "colaborador_id": emp.get("id"),
                "persona_id": emp.get("person_id"),
                "picture_url": picture_url,
                "gender": gender,
                "tipo_documento": doc_type,
                "documento": doc_num,
                "nombres": first_name,
                "primer_apellido": surname,
                "segundo_apellido": second_surname,
                "nombre_completo": full_name,
                "email_corporativo": emp.get("email"),
                "estado": emp.get("status", "active"),
                "fecha_ingreso": fecha_ingreso,
                "fecha_retiro": fecha_retiro,
                "antiguedad_dias": antiguedad["dias"],
                "antiguedad_meses": antiguedad["meses"],
                "antiguedad_anios": antiguedad["anios"],
                "empresa_id": company_id,
                "empresa_nombre": company_name,
                "area_id": area_id,
                "area_nombre": area_name,
                "cargo_id": role_id,
                "cargo_nombre": role_name,
                "centro_costos": current_job.get("cost_center_id") or "NA",
                "sede": location_name,
                "tipo_contrato": contract_type,
                "tipo_riesgo_arl": risk_type,
                "tarifa_arl_pct": tarifa_arl,
                "valor_arl_estimado": valor_arl_estimado,
                "salario_base": salario_base,
                "clasificacion_mano_obra": clasif_mo,
                "eps": str(emp.get("health_company") or "EPS Sura").replace("_", " ").title(),
                "fondo_pension": (
                    str(emp.get("pension_fund")).replace("_", " ").title()
                    if emp.get("pension_fund")
                    else (
                        "Colpensiones (Transición)"
                        if emp.get("pension_regime") == "regimen_transicion"
                        else (
                            "No Cotiza / Exento"
                            if emp.get("pension_regime") == "no_cotiza"
                            else "Protección / Porvenir"
                        )
                    )
                ),
                "banco": emp.get("bank"),
                "tipo_cuenta": emp.get("account_type"),
                "cuenta_bancaria": emp.get("account_number")
            })

        df_silver = pd.DataFrame(processed_rows)
        out_parquet = self.silver_dir / "silver_employees.parquet"
        df_silver.to_parquet(out_parquet, index=False)
        logger.info(f"Silver Employees procesado: {len(df_silver)} colaboradores guardados con foto Buk.")
        return df_silver


if __name__ == "__main__":
    p = SilverEmployeesProcessor()
    df = p.process()
    print("Muestra Silver con picture_url:")
    print(df[df["picture_url"] != ""][["documento", "nombre_completo", "picture_url"]].head(5).to_string())
