# -*- coding: utf-8 -*-
"""
Motor Especializado de Liquidaciones de Contrato y Reglas de Libranza.
Implementa las disposiciones del Código Sustantivo del Trabajo (Art. 149-153)
y las directrices operativas explicadas por Doris Elena Álvarez:
- Cesantías e Intereses son INTOCABLES ante deudas con Cooperativas y Cajas de Compensación.
- Bolsa Descontable = Salarios Pendientes + Prima de Servicios + Vacaciones Causadas.
- Generación de la Ficha Exacta de Sobrescritura en Buk en 1 Clic.
"""
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
from typing import Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent.parent
GOLD_DIR = BASE_DIR / "data" / "gold"
SILVER_DIR = BASE_DIR / "data" / "silver"

SMMLV_2026 = 1750905.0
AUX_TRANSPORTE_2026 = 249100.0


class SettlementCalculator:
    """
    Calculadora experta en liquidaciones de nómina colombiana con
    protección legal de cesantías e intereses ante cooperativas y cajas.
    """

    def __init__(self, year: int = 2026, month: int = 7):
        self.year = year
        self.month = month
        self._load_datasets()

    def _load_datasets(self):
        gold_file = GOLD_DIR / f"fact_nomina_{self.year}_{self.month:02d}.parquet"
        if gold_file.exists():
            self.df_employees = pd.read_parquet(gold_file)
        else:
            silver_file = SILVER_DIR / "silver_employees.parquet"
            self.df_employees = pd.read_parquet(silver_file) if silver_file.exists() else pd.DataFrame()

    def find_employee(self, documento: str) -> Optional[pd.Series]:
        if self.df_employees.empty:
            return None
        doc_str = str(documento).strip()
        match = self.df_employees[self.df_employees["documento"].astype(str).str.strip() == doc_str]
        if not match.empty:
            return match.iloc[0]
        match_like = self.df_employees[self.df_employees["documento"].astype(str).str.contains(doc_str)]
        return match_like.iloc[0] if not match_like.empty else None

    def calculate_settlement(
        self,
        documento: str,
        fecha_retiro: str,
        tipo_entidad: str = "cooperativa_caja",
        nombre_entidad: str = "Cooperativa / Caja de Compensación",
        valor_deuda: float = 0.0,
        ya_cobro_quincena_1: bool = True,
        nombre_entidad_2: Optional[str] = None,
        valor_deuda_2: float = 0.0
    ) -> Dict[str, Any]:
        emp = self.find_employee(documento)
        if emp is None:
            raise ValueError(f"Colaborador con documento {documento} no fue encontrado en la nómina.")

        salario_base = float(emp.get("salario_base") or SMMLV_2026)
        aux_transporte = AUX_TRANSPORTE_2026 if salario_base <= (2 * SMMLV_2026) else 0.0
        base_prestaciones = salario_base + aux_transporte

        dt_retiro = datetime.strptime(fecha_retiro[:10], "%Y-%m-%d")
        fecha_ingreso_raw = str(emp.get("fecha_ingreso") or f"{dt_retiro.year}-01-01")[:10]
        try:
            dt_ingreso = datetime.strptime(fecha_ingreso_raw, "%Y-%m-%d")
        except Exception:
            dt_ingreso = datetime(dt_retiro.year, 1, 1)

        # 1. Días en el año (Cesantías e Intereses)
        inicio_ano = max(datetime(dt_retiro.year, 1, 1), dt_ingreso)
        meses_ano = dt_retiro.month - inicio_ano.month
        dia_ret = min(dt_retiro.day, 30)
        dia_ing = min(inicio_ano.day, 30)
        dias_ano = max(1, meses_ano * 30 + (dia_ret - dia_ing + 1))

        # 2. Días en el semestre (Prima de Servicios)
        semestre_inicio_mes = 1 if dt_retiro.month <= 6 else 7
        inicio_semestre = max(datetime(dt_retiro.year, semestre_inicio_mes, 1), dt_ingreso)
        meses_sem = dt_retiro.month - inicio_semestre.month
        dias_semestre = max(1, meses_sem * 30 + (dia_ret - min(inicio_semestre.day, 30) + 1))

        # 3. Días pendientes de salario en el mes
        dia_efectivo = dt_retiro.day
        if dia_efectivo > 15 and ya_cobro_quincena_1:
            dias_pendientes_salario = min(dia_efectivo, 30) - 15
            quincena_pagada_nota = f"1Q (días 1 al 15) ya cancelada en nómina ordinaria. Liquidando {dias_pendientes_salario} días de la 2Q."
        else:
            dias_pendientes_salario = min(dia_efectivo, 30)
            quincena_pagada_nota = f"Liquidando {dias_pendientes_salario} días completos del mes."

        # 4. Saldo estimado de vacaciones
        dias_vacaciones_causadas = round((dias_ano * 15.0) / 360.0, 2)
        saldo_vac_db = float(emp.get("saldo_vacaciones_legales") or 0.0)
        dias_vacaciones = saldo_vac_db if saldo_vac_db > 0 else dias_vacaciones_causadas

        # Liquidación de Conceptos Brutos
        cesantias = round((base_prestaciones * dias_ano) / 360.0, 2)
        intereses_cesantias = round((cesantias * dias_ano * 0.12) / 360.0, 2)
        prima = round((base_prestaciones * dias_semestre) / 360.0, 2)
        vacaciones = round((salario_base * dias_vacaciones) / 30.0, 2)
        salario_pendiente = round((salario_base / 30.0) * dias_pendientes_salario, 2)
        aux_transp_pendiente = round((aux_transporte / 30.0) * dias_pendientes_salario, 2) if aux_transporte > 0 else 0.0

        # Deducciones de Ley (Salud y Pensión 4%)
        deduccion_salud = round(salario_pendiente * 0.04, 2)
        deduccion_pension = round(salario_pendiente * 0.04, 2)
        total_deducciones_ley = deduccion_salud + deduccion_pension

        # BOLSAS
        bolsa_protegida = round(cesantias + intereses_cesantias, 2)
        ingresos_descontables_brutos = salario_pendiente + aux_transp_pendiente + prima + vacaciones
        bolsa_descontable = round(max(0.0, ingresos_descontables_brutos - total_deducciones_ley), 2)
        total_bruto = round(bolsa_protegida + ingresos_descontables_brutos, 2)

        deuda_solicitada = float(valor_deuda)
        tipo = tipo_entidad.lower().strip()
        es_banco = "banco" in tipo
        es_simultaneas = "simultanea" in tipo or bool(nombre_entidad_2 and float(valor_deuda_2 or 0) > 0)
        es_cooperativa_o_caja = ("cooperativa" in tipo or "caja" in tipo) and not es_banco

        detalle_libranzas = []

        if es_banco:
            tope_legal = 0.0
            descuento_aplicado = 0.0
            deuda_remanente = deuda_solicitada
            cesantias_afectadas = 0.0
            alerta_legal = (
                f"⚠️ BANCOS NO APLICAN EN LIQUIDACIÓN: Según directriz oficial de Nómina Maaji confirmada por Doris Elena Álvarez, "
                f"las libranzas bancarias ({nombre_entidad}) NO aplican para descuento en liquidación definitiva de contrato. "
                f"El banco debe gestionar el saldo pendiente (${deuda_solicitada:,.0f} COP) directamente con el colaborador."
            )
            observacion_sobrescritura = (
                f"Sobrescribir en Buk el valor de $0 COP para la deducción de {nombre_entidad}. "
                f"Por política interna y criterio legal de Nómina Maaji, los bancos no se descuentan en la liquidación final."
            )
            detalle_libranzas.append({
                "entidad": nombre_entidad,
                "tipo": "Banco Comercial",
                "deuda_solicitada": deuda_solicitada,
                "tope_permitido": 0.0,
                "descuento_buk": 0.0,
                "saldo_remanente": deuda_solicitada,
                "nota": "Bancos no aplican para descuento por liquidación (Directriz Doris Álvarez)"
            })
        elif es_simultaneas:
            tope_legal = bolsa_descontable
            tope_por_coop = round(bolsa_descontable * 0.5, 2)
            
            entidad_1_nom = nombre_entidad or "Cooperativa 1"
            entidad_2_nom = nombre_entidad_2 or "Cooperativa 2"
            deuda_1 = deuda_solicitada
            deuda_2 = float(valor_deuda_2 or 0.0)

            desc_1 = round(min(deuda_1, tope_por_coop), 2)
            desc_2 = round(min(deuda_2, tope_por_coop), 2)
            descuento_aplicado = round(desc_1 + desc_2, 2)
            rem_1 = round(max(0.0, deuda_1 - desc_1), 2)
            rem_2 = round(max(0.0, deuda_2 - desc_2), 2)
            deuda_remanente = round(rem_1 + rem_2, 2)
            cesantias_afectadas = 0.0

            alerta_legal = (
                f"⚖️ LIBRANZAS SIMULTÁNEAS (REGLA 50/50 DORIS ÁLVAREZ): La bolsa descontable (${bolsa_descontable:,.0f} COP) "
                f"se dividió al 50% para cada cooperativa (máximo ${tope_por_coop:,.0f} COP c/u). "
                f"Cesantías e Intereses (${bolsa_protegida:,.0f} COP) quedaron 100% blindadas por ley."
            )
            observacion_sobrescritura = (
                f"Sobrescribir en Buk: {entidad_1_nom} = ${desc_1:,.0f} COP | "
                f"{entidad_2_nom} = ${desc_2:,.0f} COP. Total descontado: ${descuento_aplicado:,.0f} COP."
            )
            detalle_libranzas = [
                {
                    "entidad": entidad_1_nom,
                    "tipo": "Cooperativa 1",
                    "deuda_solicitada": deuda_1,
                    "tope_permitido": tope_por_coop,
                    "descuento_buk": desc_1,
                    "saldo_remanente": rem_1,
                    "nota": "50% de la bolsa descontable disponible"
                },
                {
                    "entidad": entidad_2_nom,
                    "tipo": "Cooperativa 2",
                    "deuda_solicitada": deuda_2,
                    "tope_permitido": tope_por_coop,
                    "descuento_buk": desc_2,
                    "saldo_remanente": rem_2,
                    "nota": "50% de la bolsa descontable disponible"
                }
            ]
        else:
            tope_legal = bolsa_descontable
            descuento_aplicado = round(min(deuda_solicitada, tope_legal), 2)
            deuda_remanente = round(max(0.0, deuda_solicitada - descuento_aplicado), 2)
            cesantias_afectadas = 0.0
            alerta_legal = (
                f"🛡️ PROTECCIÓN LEGAL APLICADA: Por ley (CST Art. 149), las Cesantías e Intereses (${bolsa_protegida:,.0f} COP) "
                f"quedaron 100% protegidas y no fueron tocadas para la deuda con {nombre_entidad}."
            )
            if deuda_remanente > 0:
                observacion_sobrescritura = (
                    f"La deuda total era ${deuda_solicitada:,.0f} COP pero la bolsa legalmente descontable solo cubría "
                    f"${tope_legal:,.0f} COP. Se debe sobrescribir en Buk el valor de ${descuento_aplicado:,.0f} COP. "
                    f"El saldo remanente (${deuda_remanente:,.0f} COP) debe ser cobrado por la entidad por fuera."
                )
            else:
                observacion_sobrescritura = f"La bolsa disponible cubrió el 100% de la cuota de {nombre_entidad}."
            
            detalle_libranzas.append({
                "entidad": nombre_entidad,
                "tipo": "Cooperativa / Caja",
                "deuda_solicitada": deuda_solicitada,
                "tope_permitido": tope_legal,
                "descuento_buk": descuento_aplicado,
                "saldo_remanente": deuda_remanente,
                "nota": "100% de la bolsa descontable disponible con cesantías blindadas"
            })

        total_neto = round(total_bruto - total_deducciones_ley - descuento_aplicado, 2)

        return {
            "colaborador": {
                "documento": str(emp.get("documento")),
                "nombre_completo": str(emp.get("nombre_completo")),
                "cargo": str(emp.get("cargo_nombre")),
                "area": str(emp.get("area_nombre")),
                "empresa": str(emp.get("empresa_nombre")),
                "salario_base": salario_base,
                "aux_transporte": aux_transporte,
                "base_prestaciones": base_prestaciones,
                "fecha_ingreso": fecha_ingreso_raw,
                "fecha_retiro": dt_retiro.strftime("%Y-%m-%d")
            },
            "tiempo_laborado": {
                "dias_ano_cesantias": dias_ano,
                "dias_semestre_prima": dias_semestre,
                "dias_pendientes_salario": dias_pendientes_salario,
                "dias_vacaciones": dias_vacaciones,
                "quincena_nota": quincena_pagada_nota
            },
            "prestaciones_brutas": {
                "cesantias": cesantias,
                "intereses_cesantias": intereses_cesantias,
                "prima_servicios": prima,
                "vacaciones": vacaciones,
                "salario_pendiente": salario_pendiente,
                "aux_transporte_pendiente": aux_transp_pendiente,
                "total_bruto": total_bruto
            },
            "deducciones_ley": {
                "salud_4pct": deduccion_salud,
                "pension_4pct": deduccion_pension,
                "total_ley": total_deducciones_ley
            },
            "bolsas_regla_doris": {
                "bolsa_protegida_cesantias": bolsa_protegida,
                "bolsa_descontable": bolsa_descontable,
                "es_cooperativa_caja": es_cooperativa_o_caja
            },
            "liquidacion_libranza": {
                "tipo_entidad": tipo_entidad,
                "nombre_entidad": nombre_entidad,
                "valor_deuda_original": deuda_solicitada,
                "tope_maximo_descontable": tope_legal,
                "valor_a_sobrescribir_buk": descuento_aplicado,
                "deuda_remanente_sin_cubrir": deuda_remanente,
                "cesantias_protegidas_intactas": bolsa_protegida,
                "alerta_legal": alerta_legal,
                "observacion_sobrescritura": observacion_sobrescritura,
                "detalle_libranzas": detalle_libranzas,
                "comprobante_nota": "Este descuento viaja automáticamente registrado en la liquidación definitiva de Buk (no requiere comprobante externo para la entidad)."
            },
            "resumen_final": {
                "total_devengado_bruto": total_bruto,
                "total_deducciones_ley": total_deducciones_ley,
                "total_deduccion_libranza": descuento_aplicado,
                "total_neto_liquidar": total_neto
            }
        }
