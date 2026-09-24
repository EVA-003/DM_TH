# -*- coding: utf-8 -*-
"""
Motor Universal de Novedades y Ajustes de Talento Humano.
Permite a solicitantes (Sebas, lideres de area y jefes de equipo) registrar cualquier tipo
de novedad (Nomina, Vacaciones, Estructura/TI, Horas Extras, Traslados) con simulacion en vivo
y aprobacion centralizada de 1 clic para Monica y Carolina.
"""
import sys
import json
from pathlib import Path
from datetime import datetime
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import GOLD_DIR, SILVER_DIR, OUTPUTS_DIR
from src.exports.report_generator import NominaReportGenerator

AJUSTES_FILE = SILVER_DIR / "adjustments_workflow.json"

SMMLV_2026 = 1750905.0
AUX_TRANSPORTE_2026 = 249100.0


class AdjustmentManager:
    def __init__(self):
        self._ensure_storage()

    def _ensure_storage(self):
        if not AJUSTES_FILE.exists():
            initial_data = [
                {
                    "id": "AJ-2026-001",
                    "solicitante": "Sebastian Gomez (Lider TI y Datos)",
                    "fecha_solicitud": "2026-07-28 09:30",
                    "categoria": "Nomina & Compensacion",
                    "tipo_novedad": "Aumento Salarial (Nivelacion de Banda)",
                    "documento": "1001394155",
                    "colaborador_nombre": "Danna Melissa Garcia Diaz",
                    "cargo": "Analista de Datos",
                    "area": "General BI",
                    "empresa": "ART MODE S.A.S BIC",
                    "valor_actual": 3000000.0,
                    "valor_propuesto": 3500000.0,
                    "delta_salario": 500000.0,
                    "delta_devengado": 500000.0,
                    "delta_carga_prestacional": 191000.0,
                    "delta_costo_maaji": 691000.0,
                    "detalle_especifico": "Nivelacion salarial por liderazgo en modelos de BI y reporteria corporativa.",
                    "justificacion": "Desempeno superior y asuncion de nuevas responsabilidades tecnicas en el equipo de Datos.",
                    "estado": "PENDIENTE",
                    "aprobado_por": None,
                    "fecha_aprobacion": None,
                    "observaciones": None
                },
                {
                    "id": "AJ-2026-002",
                    "solicitante": "Sebastian Gomez (Lider Comercial)",
                    "fecha_solicitud": "2026-07-29 14:15",
                    "categoria": "Nomina & Compensacion",
                    "tipo_novedad": "Bono de Desempeno / Proyecto",
                    "documento": "1143337302",
                    "colaborador_nombre": "Stephany Del Carmen Acosta Pernett",
                    "cargo": "Administradora Tienda",
                    "area": "Direccion de Mercados Internacionales y Retail",
                    "empresa": "MAS S.A.S BIC",
                    "valor_actual": 0.0,
                    "valor_propuesto": 450000.0,
                    "delta_salario": 0.0,
                    "delta_devengado": 450000.0,
                    "delta_carga_prestacional": 171900.0,
                    "delta_costo_maaji": 621900.0,
                    "detalle_especifico": "Incentivo por sobrecumplimiento 115% de ventas en tienda Serrezuela.",
                    "justificacion": "Cumplimiento destacado en temporada alta de Julio.",
                    "estado": "PENDIENTE",
                    "aprobado_por": None,
                    "fecha_aprobacion": None,
                    "observaciones": None
                },
                {
                    "id": "AJ-2026-003",
                    "solicitante": "Sebastian Gomez (Lider TI y Operaciones)",
                    "fecha_solicitud": "2026-07-30 11:00",
                    "categoria": "Estructura & TI",
                    "tipo_novedad": "Promocion / Cambio de Cargo",
                    "documento": "1001394155",
                    "colaborador_nombre": "Danna Melissa Garcia Diaz",
                    "cargo": "Analista de Datos",
                    "area": "General BI",
                    "empresa": "ART MODE S.A.S BIC",
                    "valor_actual": 0.0,
                    "valor_propuesto": 0.0,
                    "delta_salario": 0.0,
                    "delta_devengado": 0.0,
                    "delta_carga_prestacional": 0.0,
                    "delta_costo_maaji": 0.0,
                    "detalle_especifico": "Nuevo Cargo Propuesto: Especialista de Datos y BI Senior",
                    "justificacion": "Reestructuracion del area de Analitica para atender requerimientos de Talento Humano y Finanzas.",
                    "estado": "PENDIENTE",
                    "aprobado_por": None,
                    "fecha_aprobacion": None,
                    "observaciones": None
                }
            ]
            AJUSTES_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(AJUSTES_FILE, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, indent=2, ensure_ascii=False)

    def _read_all(self) -> list:
        self._ensure_storage()
        try:
            with open(AJUSTES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []

    def _save_all(self, data: list):
        with open(AJUSTES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def list_adjustments(self, estado: str = None) -> list:
        all_aj = self._read_all()
        if estado:
            return [a for a in all_aj if a.get("estado") == estado.upper()]
        return all_aj

    def simulate_adjustment(self, documento: str, tipo_novedad: str, valor_propuesto: float = 0.0, year: int = 2026, month: int = 7, fecha_efectiva: str = None) -> dict:
        gold_path = GOLD_DIR / f"fact_nomina_{year}_{month:02d}.parquet"
        if not gold_path.exists():
            raise FileNotFoundError("No se encontro fact_nomina")

        df = pd.read_parquet(gold_path)
        row = df[df["documento"].astype(str) == str(documento)]
        if row.empty:
            raise ValueError(f"Colaborador con documento {documento} no encontrado en la nomina activa.")

        emp = row.iloc[0]
        salario_actual = float(emp.get("salario_base", 0.0))
        devengado_actual = float(emp.get("total_devengado", 0.0))
        costo_actual = float(emp.get("costo_total_empleador", 0.0))
        tarifa_arl = float(emp.get("tarifa_arl_pct", 0.00522))

        # Cálculo de prorrateo si la fecha efectiva es a mitad de mes (ej: día 16)
        dia_inicio = 1
        dias_aplicados = 30
        factor_prorrateo = 1.0
        if fecha_efectiva:
            try:
                dt = datetime.strptime(fecha_efectiva[:10], "%Y-%m-%d")
                dia_inicio = dt.day
                if dia_inicio > 1:
                    dias_aplicados = max(1, 30 - dia_inicio + 1)
                    factor_prorrateo = dias_aplicados / 30.0
            except Exception:
                dia_inicio = 1
                factor_prorrateo = 1.0

        # Categorizar y calcular simulación exacta
        if any(w in tipo_novedad for w in ["Aumento Salarial", "Nivelacion", "Sueldo"]):
            categoria = "Nomina & Compensacion"
            nuevo_salario = float(valor_propuesto)
            delta_salario_mes = max(0.0, nuevo_salario - salario_actual)
            delta_salario = round(delta_salario_mes * factor_prorrateo, 2)
            nuevo_devengado = devengado_actual + delta_salario
            delta_devengado = delta_salario
            tasa_carga = 0.085 + 0.12 + tarifa_arl + 0.04 + 0.0833 + 0.01 + 0.0833 + 0.0417
            delta_carga = round(delta_salario * tasa_carga, 2)
            delta_costo = round(delta_salario + delta_carga, 2)
            nuevo_costo = costo_actual + delta_costo

        elif "Promocion" in tipo_novedad or "Cargo" in tipo_novedad:
            categoria = "Estructura & TI (Emplea)"
            if float(valor_propuesto) > 0 and float(valor_propuesto) > salario_actual:
                nuevo_salario = float(valor_propuesto)
                delta_salario = nuevo_salario - salario_actual
                nuevo_devengado = devengado_actual + delta_salario
                delta_devengado = delta_salario
                tasa_carga = 0.085 + 0.12 + tarifa_arl + 0.04 + 0.0833 + 0.01 + 0.0833 + 0.0417
                delta_carga = round(delta_salario * tasa_carga, 2)
                delta_costo = round(delta_salario + delta_carga, 2)
                nuevo_costo = costo_actual + delta_costo
            else:
                nuevo_salario = salario_actual
                delta_salario = 0.0
                delta_devengado = 0.0
                nuevo_devengado = devengado_actual
                delta_carga = 0.0
                delta_costo = 0.0
                nuevo_costo = costo_actual

        elif any(w in tipo_novedad for w in ["Auxilio", "Extralegal", "Rodamiento"]):
            categoria = "Nomina & Compensacion"
            nuevo_salario = salario_actual
            delta_salario = 0.0
            delta_devengado = float(valor_propuesto)
            nuevo_devengado = devengado_actual + delta_devengado
            delta_carga = 0.0  # Auxilio no constitutivo acordado según Art. 128 CST (0% parafiscales)
            delta_costo = round(delta_devengado, 2)
            nuevo_costo = costo_actual + delta_costo

        elif any(w in tipo_novedad for w in ["Bono", "Comision", "Variable"]):
            categoria = "Nomina & Compensacion"
            nuevo_salario = salario_actual
            delta_salario = 0.0
            delta_devengado = float(valor_propuesto)
            nuevo_devengado = devengado_actual + delta_devengado
            tasa_carga = 0.085 + 0.12 + tarifa_arl + 0.04 + 0.0833 + 0.01 + 0.0833
            delta_carga = round(delta_devengado * tasa_carga, 2)
            delta_costo = round(delta_devengado + delta_carga, 2)
            nuevo_costo = costo_actual + delta_costo

        elif any(w in tipo_novedad for w in ["Hora Extra", "Recargo"]):
            categoria = "Jornada & Horas Extras"
            nuevo_salario = salario_actual
            delta_salario = 0.0
            delta_devengado = float(valor_propuesto)
            nuevo_devengado = devengado_actual + delta_devengado
            tasa_carga = 0.085 + 0.12 + tarifa_arl + 0.04 + 0.0833 + 0.01 + 0.0833
            delta_carga = round(delta_devengado * tasa_carga, 2)
            delta_costo = round(delta_devengado + delta_carga, 2)
            nuevo_costo = costo_actual + delta_costo

        elif any(w in tipo_novedad for w in ["Vacacion", "Descanso"]):
            categoria = "Vacaciones & Pasivo"
            nuevo_salario = salario_actual
            delta_salario = 0.0
            delta_devengado = 0.0
            nuevo_devengado = devengado_actual
            delta_carga = 0.0
            delta_costo = 0.0
            nuevo_costo = costo_actual

        else:  # Estructura / TI / Traslados
            categoria = "Estructura & TI (Emplea)"
            nuevo_salario = salario_actual
            delta_salario = 0.0
            delta_devengado = 0.0
            nuevo_devengado = devengado_actual
            delta_carga = 0.0
            delta_costo = 0.0
            nuevo_costo = costo_actual

        return {
            "documento": str(documento),
            "colaborador_nombre": str(emp.get("nombre_completo", "")),
            "cargo": str(emp.get("cargo_nombre", "")),
            "area": str(emp.get("area_nombre", "")),
            "empresa": str(emp.get("empresa_nombre", "")),
            "categoria": categoria,
            "tipo_novedad": tipo_novedad,
            "salario_actual": salario_actual,
            "salario_nuevo": nuevo_salario,
            "delta_salario": delta_salario,
            "devengado_actual": devengado_actual,
            "devengado_nuevo": nuevo_devengado,
            "delta_devengado": delta_devengado,
            "delta_carga_prestacional": delta_carga,
            "costo_maaji_actual": costo_actual,
            "costo_maaji_nuevo": nuevo_costo,
            "delta_costo_maaji": delta_costo,
            "tarifa_arl": tarifa_arl,
            "pct_incremento": round((delta_salario / salario_actual * 100), 1) if salario_actual > 0 and delta_salario > 0 else 0.0,
            "fecha_efectiva": fecha_efectiva or f"{year}-{month:02d}-01",
            "dias_aplicados": dias_aplicados,
            "es_prorrateado": dia_inicio > 1
        }

    def submit_adjustment(self, solicitante: str, documento: str, tipo_novedad: str, valor_propuesto: float, justificacion: str, detalle_especifico: str = "", year: int = 2026, month: int = 7, fecha_efectiva: str = None) -> dict:
        sim = self.simulate_adjustment(documento, tipo_novedad, valor_propuesto, year, month, fecha_efectiva)
        all_aj = self._read_all()
        
        new_id = f"AJ-{year}-{len(all_aj) + 1:03d}"
        new_record = {
            "id": new_id,
            "solicitante": solicitante,
            "fecha_solicitud": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "categoria": sim["categoria"],
            "documento": sim["documento"],
            "colaborador_nombre": sim["colaborador_nombre"],
            "cargo": sim["cargo"],
            "area": sim["area"],
            "empresa": sim["empresa"],
            "tipo_novedad": tipo_novedad,
            "valor_actual": sim["salario_actual"] if "Aumento" in tipo_novedad else 0.0,
            "valor_propuesto": float(valor_propuesto),
            "delta_salario": sim["delta_salario"],
            "delta_devengado": sim["delta_devengado"],
            "delta_carga_prestacional": sim["delta_carga_prestacional"],
            "delta_costo_maaji": sim["delta_costo_maaji"],
            "detalle_especifico": detalle_especifico or tipo_novedad,
            "justificacion": justificacion,
            "estado": "PENDIENTE",
            "aprobado_por": None,
            "fecha_aprobacion": None,
            "observaciones": None
        }
        all_aj.append(new_record)
        self._save_all(all_aj)
        return new_record

    def approve_adjustment(self, adjustment_id: str, aprobado_por: str = "Monica / Carolina (Talento Humano)", year: int = 2026, month: int = 7) -> dict:
        all_aj = self._read_all()
        target = None
        for a in all_aj:
            if a.get("id") == adjustment_id:
                target = a
                break

        if not target:
            raise ValueError(f"Ajuste {adjustment_id} no encontrado.")

        if target.get("estado") == "APROBADO":
            return target

        target["estado"] = "APROBADO"
        target["aprobado_por"] = aprobado_por
        target["fecha_aprobacion"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        self._save_all(all_aj)

        doc = str(target["documento"])
        tipo = target.get("tipo_novedad", "")
        detalle = target.get("detalle_especifico", "")

        # 1. Aplicar cambio en Lakehouse Gold (fact_nomina)
        gold_path = GOLD_DIR / f"fact_nomina_{year}_{month:02d}.parquet"
        if gold_path.exists():
            df = pd.read_parquet(gold_path)
            idx = df[df["documento"].astype(str) == doc].index
            if not idx.empty:
                i = idx[0]
                if target.get("delta_salario", 0) > 0:
                    df.at[i, "salario_base"] = float(target["valor_propuesto"])
                
                if target.get("delta_devengado", 0) > 0:
                    df.at[i, "total_devengado"] = float(df.at[i, "total_devengado"]) + float(target["delta_devengado"])
                    if any(b in tipo for b in ["Bono", "Comision", "Variable", "Extralegal"]):
                        curr_com = float(df.at[i, "comisiones"]) if "comisiones" in df.columns and pd.notna(df.at[i, "comisiones"]) else 0.0
                        df.at[i, "comisiones"] = curr_com + float(target["delta_devengado"])
                    elif any(h in tipo for h in ["Hora Extra", "Recargo"]):
                        curr_he = float(df.at[i, "horas_extras"]) if "horas_extras" in df.columns and pd.notna(df.at[i, "horas_extras"]) else 0.0
                        df.at[i, "horas_extras"] = curr_he + float(target["delta_devengado"])

                if target.get("delta_carga_prestacional", 0) > 0:
                    curr_carga = float(df.at[i, "total_carga_prestacional"]) if "total_carga_prestacional" in df.columns and pd.notna(df.at[i, "total_carga_prestacional"]) else 0.0
                    df.at[i, "total_carga_prestacional"] = curr_carga + float(target["delta_carga_prestacional"])

                if target.get("delta_costo_maaji", 0) > 0:
                    curr_costo = float(df.at[i, "costo_total_empleador"]) if "costo_total_empleador" in df.columns and pd.notna(df.at[i, "costo_total_empleador"]) else 0.0
                    df.at[i, "costo_total_empleador"] = curr_costo + float(target["delta_costo_maaji"])

                # Promoción / Cambio de Cargo
                if any(p in tipo for p in ["Promocion", "Cargo", "Estructura"]):
                    if "Nuevo Cargo Propuesto:" in detalle:
                        new_cargo = detalle.split("Nuevo Cargo Propuesto:")[-1].strip()
                        df.at[i, "cargo_nombre"] = new_cargo
                    elif "Nuevo Cargo:" in detalle:
                        new_cargo = detalle.split("Nuevo Cargo:")[-1].strip()
                        df.at[i, "cargo_nombre"] = new_cargo

                # Traslado de Área
                if any(t in tipo for t in ["Traslado", "Area", "Centro"]):
                    if "Nueva Area Propuesta:" in detalle:
                        new_area = detalle.split("Nueva Area Propuesta:")[-1].strip()
                        df.at[i, "area_nombre"] = new_area

                df.to_parquet(gold_path, index=False)

        # 2. Sincronizar Silver Employees
        emp_path = SILVER_DIR / "silver_employees.parquet"
        if emp_path.exists():
            df_emp = pd.read_parquet(emp_path)
            idx_emp = df_emp[df_emp["documento"].astype(str) == doc].index
            if not idx_emp.empty:
                ie = idx_emp[0]
                if target.get("delta_salario", 0) > 0:
                    df_emp.at[ie, "salario_base"] = float(target["valor_propuesto"])
                if any(p in tipo for p in ["Promocion", "Cargo", "Estructura"]):
                    if "Nuevo Cargo Propuesto:" in detalle:
                        df_emp.at[ie, "cargo_nombre"] = detalle.split("Nuevo Cargo Propuesto:")[-1].strip()
                if any(t in tipo for t in ["Traslado", "Area", "Centro"]):
                    if "Nueva Area Propuesta:" in detalle:
                        df_emp.at[ie, "area_nombre"] = detalle.split("Nueva Area Propuesta:")[-1].strip()
                df_emp.to_parquet(emp_path, index=False)

        # 3. Sincronizar Silver Vacations (Recalcular pasivo con nuevo salario si aplica)
        vac_path = SILVER_DIR / "silver_vacations_by_leader.parquet"
        if vac_path.exists() and target.get("delta_salario", 0) > 0:
            df_vac = pd.read_parquet(vac_path)
            idx_vac = df_vac[df_vac["documento"].astype(str) == doc].index
            if not idx_vac.empty:
                iv = idx_vac[0]
                nuevo_sal = float(target["valor_propuesto"])
                dias = float(df_vac.at[iv, "saldo_vacaciones_legales"])
                df_vac.at[iv, "pasivo_estimado"] = round((nuevo_sal / 30.0) * dias, 2)
                df_vac.to_parquet(vac_path, index=False)

        # 4. Regenerar libro oficial de Excel TH (33 columnas con fórmulas activas)
        NominaReportGenerator().generate_excel_report(year, month)
        return target

    def reject_adjustment(self, adjustment_id: str, rechazado_por: str = "Talento Humano", motivo: str = "No procede por presupuesto") -> dict:
        all_aj = self._read_all()
        target = None
        for a in all_aj:
            if a.get("id") == adjustment_id:
                target = a
                break

        if not target:
            raise ValueError(f"Ajuste {adjustment_id} no encontrado.")

        target["estado"] = "RECHAZADO"
        target["aprobado_por"] = rechazado_por
        target["fecha_aprobacion"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        target["observaciones"] = motivo
        self._save_all(all_aj)
        return target
