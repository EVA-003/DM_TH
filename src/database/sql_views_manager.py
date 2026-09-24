import sqlite3
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SQLViewsManager")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
GOLD_DIR = BASE_DIR / "data" / "gold"
SILVER_DIR = BASE_DIR / "data" / "silver"
SQL_DIR = BASE_DIR / "data" / "sql"
SQL_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = GOLD_DIR / "maaji_talento_humano.db"
SQL_SCRIPT_PATH = SQL_DIR / "maaji_vistas_talento_humano.sql"

SQL_DDL_AND_VIEWS = """-- ====================================================================
-- MAAJI TALENTO HUMANO - MODELO DIMENSIONAL & VISTAS SQL EMPRESARIALES
-- ====================================================================
-- Generado automáticamente para resguardo, reportería BI y conciliación
-- Base de Datos: maaji_talento_humano
-- ====================================================================

-- 1. VISTA: Nómina Consolidada de Cierre (Sábana Maestra)
DROP VIEW IF EXISTS vw_nomina_cierre_consolidado;
CREATE VIEW vw_nomina_cierre_consolidado AS
SELECT 
    f.colaborador_id,
    f.tipo_documento,
    f.documento AS cedula,
    f.nombre_completo,
    f.empresa_nombre AS empresa,
    f.area_nombre AS area,
    f.cargo_nombre AS cargo,
    f.centro_costos,
    f.sede,
    f.clasificacion_mano_obra AS mano_obra,
    f.tipo_contrato,
    f.fecha_ingreso,
    ROUND(f.antiguedad_meses, 1) AS antiguedad_meses,
    f.salario_base,
    f.comisiones,
    f.horas_extras,
    f.otros_devengados,
    f.total_devengado,
    f.tarifa_arl_pct,
    f.seguridad_social_arl AS aporte_arl,
    f.total_carga_prestacional AS carga_prestacional_38pct,
    f.costo_total_empleador AS costo_total_compania,
    f.eps,
    f.fondo_pension,
    f.periodo_corte
FROM fact_nomina f;

-- 2. VISTA: Resumen Ejecutivo de Costos por Razón Social
DROP VIEW IF EXISTS vw_resumen_costos_empresa;
CREATE VIEW vw_resumen_costos_empresa AS
SELECT 
    empresa_nombre AS empresa,
    COUNT(DISTINCT colaborador_id) AS headcount_activos,
    SUM(salario_base) AS total_masa_salarial_base,
    SUM(comisiones) AS total_comisiones,
    SUM(horas_extras) AS total_horas_extras,
    SUM(total_devengado) AS total_devengado,
    SUM(total_carga_prestacional) AS total_carga_prestacional,
    SUM(costo_total_empleador) AS costo_total_compania,
    ROUND(SUM(costo_total_empleador) * 100.0 / (SELECT SUM(costo_total_empleador) FROM fact_nomina), 2) AS participacion_costo_pct
FROM fact_nomina
GROUP BY empresa_nombre;

-- 3. VISTA: Distribución de Costos por Mano de Obra (MOD vs MOI)
DROP VIEW IF EXISTS vw_resumen_mano_obra;
CREATE VIEW vw_resumen_mano_obra AS
SELECT 
    clasificacion_mano_obra AS clasificacion_costo,
    COUNT(DISTINCT colaborador_id) AS headcount,
    SUM(salario_base) AS masa_salarial,
    SUM(horas_extras) AS horas_extras_totales,
    SUM(costo_total_empleador) AS costo_total,
    ROUND(SUM(costo_total_empleador) * 100.0 / (SELECT SUM(costo_total_empleador) FROM fact_nomina), 2) AS participacion_pct
FROM fact_nomina
GROUP BY clasificacion_mano_obra;

-- 4. VISTA: Radar de Vacaciones y Pasivo Laboral por Líder (Carolina)
DROP VIEW IF EXISTS vw_radar_vacaciones_lideres;
CREATE VIEW vw_radar_vacaciones_lideres AS
SELECT 
    supervisor_nombre AS lider_supervisor,
    COUNT(colaborador_id) AS colaboradores_a_cargo,
    SUM(CASE WHEN dias_acumulados >= 18.0 THEN 1 ELSE 0 END) AS colaboradores_criticos_mas_18d,
    SUM(CASE WHEN dias_acumulados >= 12.0 AND dias_acumulados < 18.0 THEN 1 ELSE 0 END) AS colaboradores_alerta_12_a_18d,
    ROUND(AVG(dias_acumulados), 1) AS promedio_dias_acumulados,
    SUM(pasivo_estimado_cop) AS pasivo_total_cop,
    SUM(pasivo_proyectado_corte_cop) AS pasivo_proyectado_corte_cop
FROM fact_vacaciones
GROUP BY supervisor_nombre;

-- 5. VISTA: Consolidado Oficial de Novedades TI (Emplea)
DROP VIEW IF EXISTS vw_novedades_ti_emplea;
CREATE VIEW vw_novedades_ti_emplea AS
SELECT 
    movimiento AS tipo_movimiento,
    documento AS cedula,
    nombre_completo,
    cargo_nombre AS cargo,
    area_nombre AS area,
    empresa_nombre AS empresa,
    sede,
    email_corporativo,
    fecha_efectiva,
    estado_gestion
FROM fact_novedades_ti;

-- 6. VISTA: Auditoría Legal de Horas Extras (Límites CST Colombia)
DROP VIEW IF EXISTS vw_auditoria_horas_extras_legal;
CREATE VIEW vw_auditoria_horas_extras_legal AS
SELECT 
    documento AS cedula,
    nombre_completo,
    empresa_nombre AS empresa,
    area_nombre AS area,
    cargo_nombre AS cargo,
    horas_extras AS valor_horas_extras_cop,
    salario_base,
    ROUND((horas_extras / NULLIF(salario_base, 0)) * 100.0, 2) AS impacto_horas_extras_sobre_salario_pct,
    CASE 
        WHEN horas_extras > 1000000 THEN 'ALERTA_ALTO_VOLUMEN'
        WHEN horas_extras > 500000 THEN 'REVISION_SUPERVISOR'
        WHEN horas_extras > 0 THEN 'DENTRO_RANGO_OPERATIVO'
        ELSE 'SIN_EXTRAS'
    END AS estado_auditoria_legal
FROM fact_nomina
WHERE horas_extras > 0;

-- 7. VISTA: Personal Temporal (Empresas de Servicios Temporales - EST)
DROP VIEW IF EXISTS vw_personal_temporal_est;
CREATE VIEW vw_personal_temporal_est AS
SELECT 
    documento AS cedula,
    nombre_completo,
    empresa_nombre AS empresa,
    area_nombre AS area_o_tienda,
    cargo_nombre AS cargo,
    lider_supervisor AS lider,
    estado AS estado_contrato,
    salario_base,
    fecha_ingreso,
    fecha_retiro,
    centro_costos AS ceco,
    tipo_vinculacion
FROM fact_personal_temporal;
"""

class SQLViewsManager:
    def __init__(self):
        self.db_path = DB_PATH
        self.sql_script_path = SQL_SCRIPT_PATH

    def sync_to_sql_database(self, year: int = 2026, month: int = 7) -> str:
        logger.info(f"Sincronizando Datamart a Base de Datos SQLite y Vistas SQL: {self.db_path}...")
        
        # 1. Cargar tablas Gold
        fact_nomina_file = GOLD_DIR / f"fact_nomina_{year}_{month:02d}.parquet"
        fact_vacaciones_file = GOLD_DIR / "fact_vacaciones_pasivo.parquet"
        
        df_nomina = pd.read_parquet(fact_nomina_file) if fact_nomina_file.exists() else pd.DataFrame()
        df_vacaciones = pd.read_parquet(fact_vacaciones_file) if fact_vacaciones_file.exists() else pd.DataFrame()
        
        # Cargar novedades TI
        silver_ti_file = SILVER_DIR / "silver_ti_novedades.parquet"
        df_ti = pd.read_parquet(silver_ti_file) if silver_ti_file.exists() else pd.DataFrame()

        # Cargar personal temporal
        silver_temp_file = SILVER_DIR / "silver_temporales.parquet"
        df_temp = pd.read_parquet(silver_temp_file) if silver_temp_file.exists() else pd.DataFrame()

        # 2. Conectar a SQLite
        conn = sqlite3.connect(str(self.db_path))
        
        # Persistir tablas físicas
        if not df_nomina.empty:
            df_nomina.to_sql("fact_nomina", conn, if_exists="replace", index=False)
            logger.info(f"Tabla fact_nomina persistida ({len(df_nomina)} registros).")
            
        if not df_vacaciones.empty:
            df_vacaciones.to_sql("fact_vacaciones", conn, if_exists="replace", index=False)
            logger.info(f"Tabla fact_vacaciones persistida ({len(df_vacaciones)} registros).")
            
        if not df_ti.empty:
            df_ti.to_sql("fact_novedades_ti", conn, if_exists="replace", index=False)
            logger.info(f"Tabla fact_novedades_ti persistida ({len(df_ti)} registros).")

        if not df_temp.empty:
            df_temp.to_sql("fact_personal_temporal", conn, if_exists="replace", index=False)
            logger.info(f"Tabla fact_personal_temporal persistida ({len(df_temp)} registros).")

        # 3. Ejecutar creación de Vistas SQL
        cursor = conn.cursor()
        cursor.executescript(SQL_DDL_AND_VIEWS)
        conn.commit()
        conn.close()
        
        # 4. Guardar archivo de script SQL exportable
        with open(self.sql_script_path, "w", encoding="utf-8") as f:
            f.write(SQL_DDL_AND_VIEWS)
            
        logger.info(f"Vistas SQL creadas y script exportado en: {self.sql_script_path}")
        return str(self.db_path)

if __name__ == "__main__":
    mgr = SQLViewsManager()
    mgr.sync_to_sql_database()
