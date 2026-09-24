# -*- coding: utf-8 -*-
"""
Motor de Generación de Informes Oficiales de Nómina en Excel.
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import logging
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from config.settings import GOLD_DIR, OUTPUTS_DIR

logger = logging.getLogger("ReportGenerator")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class NominaReportGenerator:
    def __init__(self):
        self.gold_dir = GOLD_DIR
        self.outputs_dir = OUTPUTS_DIR

    def generate_excel_report(self, year: int = 2026, month: int = 7, custom_columns: list = None) -> Path:
        from datetime import datetime
        gold_path = self.gold_dir / f"fact_nomina_{year}_{month:02d}.parquet"
        if not gold_path.exists():
            raise FileNotFoundError(f"No se encontró la tabla Gold para {year}-{month:02d} en {gold_path}")

        df = pd.read_parquet(gold_path).copy()

        # Incorporar columnas dinámicas en el DataFrame si existen
        if custom_columns:
            for cc in custom_columns:
                c_id = cc["column_id"]
                vals = cc.get("values_by_doc", {})
                df[c_id] = df["documento"].astype(str).map(vals).fillna(0.0)
                if cc.get("is_constitutivo", False):
                    df["total_devengado"] = df["total_devengado"] + df[c_id]
                    df["costo_total_empleador"] = df["costo_total_empleador"] + (df[c_id] * 1.5183)

        output_excel = self.outputs_dir / f"Informe_Gestion_Nomina_{year}_{month:02d}.xlsx"
        logger.info(f"Generando libro oficial de Excel en {output_excel.name} con formato TH...")

        # Ordenar por empresa y nombre
        df.sort_values(by=["empresa_nombre", "primer_apellido", "nombres"], inplace=True)
        df.reset_index(drop=True, inplace=True)

        wb = openpyxl.Workbook()

        # Estilos corporativos Maaji
        font_bold = Font(name="Calibri", size=10, bold=True)
        font_normal = Font(name="Calibri", size=10)
        border_thin = Border(
            left=Side(style="thin", color="CBD5E1"),
            right=Side(style="thin", color="CBD5E1"),
            top=Side(style="thin", color="CBD5E1"),
            bottom=Side(style="thin", color="CBD5E1")
        )

        # -------------------------------------------------------------------------
        # 1. HOJA: Datos (Parámetros Legales, ARL, Seguridad Social y Prestaciones)
        # -------------------------------------------------------------------------
        ws_datos = wb.active
        ws_datos.title = "Datos "
        ws_datos.views.sheetView[0].showGridLines = True

        ws_datos.cell(1, 1, "Seguridad Social ").font = Font(name="Calibri", size=11, bold=True)
        ws_datos.cell(2, 2, "Empleado").font = font_bold
        ws_datos.cell(2, 3, "Empleador ").font = font_bold
        ws_datos.cell(2, 4, "Total ").font = font_bold

        ws_datos.cell(3, 1, "Salud").font = font_normal
        ws_datos.cell(3, 2, 0.04).number_format = "0.0%"
        ws_datos.cell(3, 3, 0.085).number_format = "0.0%"
        ws_datos.cell(3, 4, 0.125).number_format = "0.0%"

        ws_datos.cell(4, 1, "Pensión ").font = font_normal
        ws_datos.cell(4, 2, 0.04).number_format = "0.0%"
        ws_datos.cell(4, 3, 0.12).number_format = "0.0%"
        ws_datos.cell(4, 4, 0.16).number_format = "0.0%"

        ws_datos.cell(5, 1, "ARL Riesgo 1").font = font_normal
        ws_datos.cell(5, 2, 0.0).number_format = "0.0%"
        ws_datos.cell(5, 3, 0.00522).number_format = "0.00000"

        ws_datos.cell(6, 1, "ARL Riesgo II").font = font_normal
        ws_datos.cell(6, 3, 0.01044).number_format = "0.00000"

        ws_datos.cell(7, 1, "ARL Riesgo IV").font = font_normal
        ws_datos.cell(7, 3, 0.0435).number_format = "0.00000"

        ws_datos.cell(8, 1, "Caja de compensación ").font = font_normal
        ws_datos.cell(8, 2, 0.0).number_format = "0.0%"
        ws_datos.cell(8, 3, 0.04).number_format = "0.0%"

        ws_datos.cell(9, 1, "ICBF (Solo salario integral)").font = font_normal
        ws_datos.cell(9, 2, 0.0).number_format = "0.0%"
        ws_datos.cell(9, 3, 0.03).number_format = "0.0%"
        ws_datos.cell(9, 4, 0.03).number_format = "0.0%"

        ws_datos.cell(10, 1, "SENA (Solo salario integral)").font = font_normal
        ws_datos.cell(10, 2, 0.0).number_format = "0.0%"
        ws_datos.cell(10, 3, 0.02).number_format = "0.0%"
        ws_datos.cell(10, 4, 0.02).number_format = "0.0%"

        ws_datos.cell(12, 1, "Provisión mensual de prestaciones sociales ").font = Font(name="Calibri", size=11, bold=True)
        ws_datos.cell(13, 1, "Cesantias ").font = font_normal
        ws_datos.cell(13, 3, 0.0833).number_format = "0.00%"
        ws_datos.cell(13, 4, 0.0833).number_format = "0.00%"

        ws_datos.cell(14, 1, "Intereses a las cesantias ").font = font_normal
        ws_datos.cell(14, 3, 0.01).number_format = "0.00%"
        ws_datos.cell(14, 4, 0.01).number_format = "0.00%"

        ws_datos.cell(15, 1, "Prima ").font = font_normal
        ws_datos.cell(15, 3, 0.0833).number_format = "0.00%"
        ws_datos.cell(15, 4, 0.0833).number_format = "0.00%"

        ws_datos.cell(16, 1, "Vacaciones ").font = font_normal
        ws_datos.cell(16, 3, 0.0417).number_format = "0.00%"
        ws_datos.cell(16, 4, 0.0417).number_format = "0.00%"

        # Parámetros salariales y Auxilio de transporte
        ws_datos.cell(13, 6, "Auxilio de transporte").font = font_bold
        ws_datos.cell(13, 9, 200000).number_format = "$#,##0"
        ws_datos.cell(13, 10, 249100).number_format = "$#,##0" # J13 = 249,100

        ws_datos.cell(14, 6, "SMMLV").font = font_bold
        ws_datos.cell(14, 9, 1423500).number_format = "$#,##0"
        ws_datos.cell(14, 10, 1750905).number_format = "$#,##0" # J14 = 1,750,905

        ws_datos.cell(3, 15, 1750905).number_format = "$#,##0"  # O3 = SMMLV 2026 para tope auxilio
        ws_datos.cell(3, 16, 1750905).number_format = "$#,##0"

        ws_datos.cell(19, 1, "Auxilio Transporte Legal ").font = font_bold
        ws_datos.cell(19, 2, 249100).number_format = "$#,##0"

        # -------------------------------------------------------------------------
        # 2. HOJA: Nomina {Mes} (33 Columnas Oficiales TH + Auditoría HE)
        # -------------------------------------------------------------------------
        mes_nombre = {
            1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
            5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
            9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        }.get(month, f"Mes{month}")

        ws_nom = wb.create_sheet(title=f"Nomina {mes_nombre}")
        ws_nom.views.sheetView[0].showGridLines = True

        headers_33 = [
            "",                                      # Col A (1)
            "ID Empleado ",                          # Col B (2)
            "Empresa ",                              # Col C (3)
            " Nombre Completo Empleado ",             # Col D (4)
            "Cargo",                                 # Col E (5)
            " Nombre Área",                          # Col F (6)
            "Fecha Ingreso \nCompañía",              # Col G (7)
            "Fecha de Corte\n (Para definir Antigüedad)", # Col H (8)
            "Antigüedad * Años  ",                   # Col I (9)
            " Tipo de Contrato",                     # Col J (10)
            " Sueldo Base 2025",                     # Col K (11)
            " Sueldo Base 2026",                     # Col L (12)
            " Sueldo Base 2026 Prop",                # Col M (13)
            "Porcentaje Aumento Salario Base",       # Col N (14)
            " Salud Empleador",                      # Col O (15)
            "Pensión Empleador",                     # Col P (16)
            " Riesgos Laborales",                    # Col Q (17)
            "Tasa Riesgos Laborales",                # Col R (18)
            " Caja Compensación Familiar",           # Col S (19)
            "ICBF",                                  # Col T (20)
            "SENA",                                  # Col U (21)
            " Cesantías",                            # Col V (22)
            " Interés Cesantías",                    # Col W (23)
            " Prima Legal",                          # Col X (24)
            "Vacaciones Definitivas",                # Col Y (25)
            "Auxilio De Transporte Legal ",          # Col Z (26)
            " Auxilio De Rodamiento",                # Col AA (27)
            " Auxilio De Transporte Extralegal",     # Col AB (28)
            "Administración Temporal ",              # Col AC (29)
            "Total Hora Extra ",                     # Col AD (30)
            "Total Comisiones ",                     # Col AE (31)
            "Total 2026 Costo Maaji",                # Col AF (32)
            "Total 2026 Devengado",                  # Col AG (33)
            "Auditoría Legal HE (CST Art. 159)"      # Col AH (34)
        ]

        header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        header_font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")

        for c_idx, h_text in enumerate(headers_33, start=1):
            cell = ws_nom.cell(row=1, column=c_idx, value=h_text)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = border_thin

        cutoff_date = datetime(year, month, 30 if month != 2 else 28)

        for r_idx, row in df.iterrows():
            excel_row = r_idx + 2

            f_ing = row.get("fecha_ingreso")
            if isinstance(f_ing, str):
                try:
                    f_ing_dt = datetime.strptime(f_ing[:10], "%Y-%m-%d")
                except:
                    f_ing_dt = None
            else:
                f_ing_dt = f_ing

            salario_2026 = float(row.get("salario_base", 0.0))
            salario_2025 = round(salario_2026 / 1.0509996, 2)
            tarifa_arl = float(row.get("tarifa_arl_pct", 0.00522))
            he_val = float(row.get("horas_extras", 0.0))
            com_val = float(row.get("comisiones", 0.0))

            ws_nom.cell(excel_row, 1, None).border = border_thin
            ws_nom.cell(excel_row, 2, str(row.get("documento", ""))).border = border_thin
            ws_nom.cell(excel_row, 3, str(row.get("empresa_nombre", ""))).border = border_thin
            ws_nom.cell(excel_row, 4, str(row.get("nombre_completo", ""))).border = border_thin
            ws_nom.cell(excel_row, 5, str(row.get("cargo_nombre", ""))).border = border_thin
            ws_nom.cell(excel_row, 6, str(row.get("area_nombre", ""))).border = border_thin

            c_g = ws_nom.cell(excel_row, 7, f_ing_dt)
            c_g.number_format = "YYYY-MM-DD"
            c_g.border = border_thin

            c_h = ws_nom.cell(excel_row, 8, cutoff_date)
            c_h.number_format = "YYYY-MM-DD"
            c_h.border = border_thin

            c_i = ws_nom.cell(excel_row, 9, f"=(DAYS360(G{excel_row},H{excel_row})+1)/360")
            c_i.number_format = "0.00"
            c_i.border = border_thin

            ws_nom.cell(excel_row, 10, str(row.get("tipo_contrato", "Indefinido"))).border = border_thin

            c_k = ws_nom.cell(excel_row, 11, salario_2025)
            c_k.number_format = "$#,##0"
            c_k.border = border_thin

            c_l = ws_nom.cell(excel_row, 12, salario_2026)
            c_l.number_format = "$#,##0"
            c_l.border = border_thin

            c_m = ws_nom.cell(excel_row, 13, salario_2026)
            c_m.number_format = "$#,##0"
            c_m.border = border_thin

            c_n = ws_nom.cell(excel_row, 14, f"=+(L{excel_row}/K{excel_row})-1")
            c_n.number_format = "0.0%"
            c_n.border = border_thin

            c_o = ws_nom.cell(excel_row, 15, f"=+L{excel_row}*'Datos '!$C$3")
            c_o.number_format = "$#,##0"
            c_o.border = border_thin

            c_p = ws_nom.cell(excel_row, 16, f"=+L{excel_row}*'Datos '!$C$4")
            c_p.number_format = "$#,##0"
            c_p.border = border_thin

            c_q = ws_nom.cell(excel_row, 17, f"=+L{excel_row}*R{excel_row}")
            c_q.number_format = "$#,##0"
            c_q.border = border_thin

            c_r = ws_nom.cell(excel_row, 18, tarifa_arl)
            c_r.number_format = "0.00000"
            c_r.border = border_thin

            c_s = ws_nom.cell(excel_row, 19, f"=+L{excel_row}*'Datos '!$C$8")
            c_s.number_format = "$#,##0"
            c_s.border = border_thin

            c_t = ws_nom.cell(excel_row, 20, 0.0)
            c_t.number_format = "$#,##0"
            c_t.border = border_thin

            c_u = ws_nom.cell(excel_row, 21, 0.0)
            c_u.number_format = "$#,##0"
            c_u.border = border_thin

            c_v = ws_nom.cell(excel_row, 22, f"=+L{excel_row}*'Datos '!$C$13")
            c_v.number_format = "$#,##0"
            c_v.border = border_thin

            c_w = ws_nom.cell(excel_row, 23, f"=+L{excel_row}*'Datos '!$C$14")
            c_w.number_format = "$#,##0"
            c_w.border = border_thin

            c_x = ws_nom.cell(excel_row, 24, f"=+L{excel_row}*'Datos '!$C$15")
            c_x.number_format = "$#,##0"
            c_x.border = border_thin

            c_y = ws_nom.cell(excel_row, 25, f"=+L{excel_row}*'Datos '!$C$16")
            c_y.number_format = "$#,##0"
            c_y.border = border_thin

            c_z = ws_nom.cell(excel_row, 26, f"=+IF(L{excel_row}<=2*'Datos '!$O$3,'Datos '!$J$13,0)")
            c_z.number_format = "$#,##0"
            c_z.border = border_thin

            c_aa = ws_nom.cell(excel_row, 27, 0.0)
            c_aa.number_format = "$#,##0"
            c_aa.border = border_thin

            c_ab = ws_nom.cell(excel_row, 28, None)
            c_ab.border = border_thin

            c_ac = ws_nom.cell(excel_row, 29, None)
            c_ac.border = border_thin

            c_ad = ws_nom.cell(excel_row, 30, he_val if he_val > 0 else 0.0)
            c_ad.number_format = "$#,##0"
            c_ad.border = border_thin

            c_ae = ws_nom.cell(excel_row, 31, com_val if com_val > 0 else None)
            c_ae.number_format = "$#,##0"
            c_ae.border = border_thin

            c_af = ws_nom.cell(excel_row, 32, f"=+L{excel_row}+O{excel_row}+P{excel_row}+Q{excel_row}+S{excel_row}+V{excel_row}+W{excel_row}+X{excel_row}+Y{excel_row}+Z{excel_row}+AA{excel_row}+IF(ISBLANK(AB{excel_row}),0,AB{excel_row})+IF(ISBLANK(AC{excel_row}),0,AC{excel_row})+AD{excel_row}+IF(ISBLANK(AE{excel_row}),0,AE{excel_row})")
            c_af.number_format = "$#,##0"
            c_af.font = font_bold
            c_af.border = border_thin

            c_ag = ws_nom.cell(excel_row, 33, f"=+L{excel_row}+Z{excel_row}+AA{excel_row}+IF(ISBLANK(AB{excel_row}),0,AB{excel_row})+AD{excel_row}+IF(ISBLANK(AE{excel_row}),0,AE{excel_row})")
            c_ag.number_format = "$#,##0"
            c_ag.font = font_bold
            c_ag.border = border_thin

            # Col AH (34): Auditoría Legal Horas Extras
            c_ah = ws_nom.cell(excel_row, 34, f'=IF(AD{excel_row}>=650000, "⚠️ Alerta Legal (>12h/sem)", "✅ Conforme CST")')
            c_ah.alignment = Alignment(horizontal="center")
            c_ah.border = border_thin

        # Fila de Totales
        tot_row = len(df) + 2
        ws_nom.cell(tot_row, 4, "TOTAL GENERAL").font = font_bold
        ws_nom.cell(tot_row, 4).alignment = Alignment(horizontal="right")

        for c_idx in [11, 12, 13, 15, 16, 17, 19, 22, 23, 24, 25, 26, 27, 30, 31, 32, 33]:
            col_letter = get_column_letter(c_idx)
            c_tot = ws_nom.cell(tot_row, c_idx, f"=SUM({col_letter}2:{col_letter}{tot_row-1})")
            c_tot.font = font_bold
            c_tot.number_format = "$#,##0"
            c_tot.fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
            c_tot.border = Border(top=Side(style="thin"), bottom=Side(style="double"))

        for c in range(1, 35):
            col_letter = get_column_letter(c)
            ws_nom.column_dimensions[col_letter].width = 16
        ws_nom.column_dimensions["B"].width = 15
        ws_nom.column_dimensions["C"].width = 22
        ws_nom.column_dimensions["D"].width = 34
        ws_nom.column_dimensions["E"].width = 30
        ws_nom.column_dimensions["F"].width = 32
        ws_nom.column_dimensions["AH"].width = 26

        # -------------------------------------------------------------------------
        # 3. HOJA: Consolidado (Evolución Headcount y Costos)
        # -------------------------------------------------------------------------
        ws_cons = wb.create_sheet(title="Consolidado")
        ws_cons.views.sheetView[0].showGridLines = True

        ws_cons.cell(1, 1, "Evolucion Head Count 2026").font = font_bold
        meses_hdr = ["Mes", "Enero ", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Total"]
        for idx, m_txt in enumerate(meses_hdr, start=1):
            c = ws_cons.cell(2, idx, m_txt)
            c.font = font_bold
            c.fill = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")

        cons_rows = [
            ("Head Count Total", [344, 342, 353, 371, 359, 353, len(df)]),
            ("Costo Salarial Total", [1873414812, 1889237257, 1981171857, 2097912389, 1968619505, 1973046587, f"=SUM('Nomina {mes_nombre}'!AF2:AF{len(df)+1})"]),
            ("Costo Salarial MO Directa", [350456321, 344105198, 376152765, 397337000, 360190720, 327982503, 348794280]),
            ("Costo Salarial MO Indirecta", [1522958491, 1545132060, 1606143092, 1700575389, 1608428785, 1542365845, 1446208429]),
        ]

        for r_i, (label, vals) in enumerate(cons_rows, start=3):
            ws_cons.cell(r_i, 1, label).font = font_bold
            for c_i, val in enumerate(vals, start=2):
                cell = ws_cons.cell(r_i, c_i, val)
                if "Costo" in label:
                    cell.number_format = "$#,##0"
            if r_i == 3:
                ws_cons.cell(r_i, 10, f"=AVERAGE(B{r_i}:H{r_i})").number_format = "#,##0"
            else:
                ws_cons.cell(r_i, 10, f"=SUM(B{r_i}:H{r_i})").number_format = "$#,##0"

        # Guardar en outputs y en Downloads del usuario
        wb.save(output_excel)
        dl_path = Path(r"C:\Users\oberrio\Downloads") / f"Informe_Gestion_Nomina_{year}_{month:02d}_Oficial.xlsx"
        wb.save(dl_path)

        logger.info(f"Libro oficial de nómina TH generado exitosamente en: {output_excel} y {dl_path}")
        return output_excel


if __name__ == "__main__":
    generator = NominaReportGenerator()
    out = generator.generate_excel_report(2026, 7)
    print(f"\n[ÉXITO] Archivo Excel TH generado en: {out}")
