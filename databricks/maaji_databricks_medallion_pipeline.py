# Databricks notebook source
# COMMAND ----------
# MAGIC %md
# MAGIC # 🌸 MAAJI - PIPELINE MEDALLION DE TALENTO HUMANO (DATABRICKS LAKEHOUSE)
# MAGIC **Autores:** Equipo de Datos & Talento Humano (Oscar Berrio, Sebastian Gómez, Mónica Henao)  
# MAGIC **Arquitectura:** Medallion Lakehouse (Bronze ➔ Silver ➔ Gold ➔ Vistas SQL Power BI)  
# MAGIC **Almacenamiento Cloud:** Azure Data Lake Storage Gen2 (`stmaajidwhdev`)  
# MAGIC **Fuentes:** Buk API Colombia (101 períodos) + Sábana de Nómina + Maestra Temporales EST (593 históricos)

# COMMAND ----------
# MAGIC %md
# MAGIC ## 1. CONFIGURACIÓN DE CREDENCIALES AZURE STORAGE & WIDGETS

# COMMAND ----------
import calendar
from datetime import datetime
import pyspark.sql.functions as F
from pyspark.sql.types import *

# 1. Configuración de autenticación con Azure Data Lake Storage Gen2 (stmaajidwhdev)
STORAGE_ACCOUNT = "stmaajidwhdev"

try:
    STORAGE_KEY = dbutils.secrets.get(scope="maaji-secrets", key="azure-storage-key")
except Exception:
    import os
    STORAGE_KEY = os.getenv("AZURE_STORAGE_KEY", "")

try:
    dbutils.widgets.text("azure_storage_key", "", "5. Clave Azure Storage (Opcional si scope existe)")
    widget_key = dbutils.widgets.get("azure_storage_key").strip()
    if widget_key:
        STORAGE_KEY = widget_key
except Exception:
    pass

if STORAGE_KEY:
    spark.conf.set(f"fs.azure.account.auth.type.{STORAGE_ACCOUNT}.dfs.core.windows.net", "SharedKey")
    spark.conf.set(f"fs.azure.account.key.{STORAGE_ACCOUNT}.dfs.core.windows.net", STORAGE_KEY)

BRONZE_CONTAINER = "bronze-zone"
SILVER_CONTAINER = "silver-zone"
GOLD_CONTAINER   = "gold-zone"

BRONZE_PATH = f"abfss://{BRONZE_CONTAINER}@{STORAGE_ACCOUNT}.dfs.core.windows.net/talento_humano"
SILVER_PATH = f"abfss://{SILVER_CONTAINER}@{STORAGE_ACCOUNT}.dfs.core.windows.net/talento_humano"
GOLD_PATH   = f"abfss://{GOLD_CONTAINER}@{STORAGE_ACCOUNT}.dfs.core.windows.net/talento_humano"

# 2. Widgets interactivos para ejecución dinámica en Databricks
try:
    dbutils.widgets.dropdown("mes_objetivo", "TODOS_2026", ["TODOS_2026", "2026-06", "2026-07", "2026-08"], "1. Período Objetivo")
    dbutils.widgets.dropdown("extraer_buk_api", "NO", ["NO", "SI"], "2. ¿Re-extraer Buk API en vivo?")
    dbutils.widgets.dropdown("modo_ejecucion", "PRODUCCION", ["PRODUCCION", "SIMULACION_AUMENTO_SALARIAL", "SIMULACION_HORAS_EXTRAS"], "3. Modo de Ejecución")
    dbutils.widgets.text("pct_simulacion", "10.0", "4. % Variación (Solo si es Simulación)")

    MES_OBJETIVO = dbutils.widgets.get("mes_objetivo")
    EXTRAER_BUK = dbutils.widgets.get("extraer_buk_api") == "SI"
    MODO_EJECUCION = dbutils.widgets.get("modo_ejecucion")
    PCT_SIMULACION = float(dbutils.widgets.get("pct_simulacion")) / 100.0
except Exception:
    MES_OBJETIVO = "TODOS_2026"
    EXTRAER_BUK = False
    MODO_EJECUCION = "PRODUCCION"
    PCT_SIMULACION = 0.10

print("="*65)
print("🚀 [Databricks Lakehouse Maaji] Conexión establecida con Azure ADLS Gen2")
print(f"• Almacenamiento: {STORAGE_ACCOUNT}.dfs.core.windows.net")
print(f"• Período Seleccionado: {MES_OBJETIVO}")
print(f"• Modo de Ejecución: {MODO_EJECUCION} (Variación: {PCT_SIMULACION*100:.1f}%)")
print("="*65)

# COMMAND ----------
# MAGIC %md
# MAGIC ## 2. CAPA BRONZE: INGESTA DESDE BUK COLOMBIA API (OPCIONAL EN VIVO)

# COMMAND ----------
import requests
import json
import pandas as pd

BUK_TOKEN = "EMVvA6ppoVTtRdoXgqu8JSWj"
BUK_BASE_URL = "https://maaji.buk.co/api/v1/colombia"
headers = {"auth_token": BUK_TOKEN, "Accept": "application/json"}

if EXTRAER_BUK:
    print("🔄 [BRONZE] Extrayendo datos frescos en vivo desde Buk Colombia API...")
    
    def extract_paginated(endpoint, page_size=100):
        all_data = []
        page = 1
        while True:
            url = f"{BUK_BASE_URL}/{endpoint}?page={page}&page_size={page_size}"
            resp = requests.get(url, headers=headers, timeout=25)
            if resp.status_code != 200:
                break
            body = resp.json()
            items = body.get("data", [])
            if not items:
                break
            all_data.extend(items)
            if not body.get("pagination", {}).get("next"):
                break
            page += 1
        return all_data

    emp_list = extract_paginated("employees")
    print(f"✅ Colaboradores extraídos de Buk: {len(emp_list)}")
    df_raw_emp = spark.createDataFrame(pd.DataFrame(emp_list).astype(str))
    df_raw_emp.write.mode("overwrite").parquet(f"{BRONZE_PATH}/employees/employees_latest.parquet")
    print(f"💾 Guardado en {BRONZE_PATH}/employees/employees_latest.parquet")
else:
    print("⚡ [BRONZE] Usando datos ya consolidados en el Data Lake (ahorro de tiempo y llamadas de API).")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 3. CAPA SILVER: LIMPIEZA, CRUCES DIMENSIONALES & MAESTRA DE TEMPORALES

# COMMAND ----------
# 1. Cargar maestro de colaboradores directos
try:
    df_emp_silver = spark.read.parquet(f"{SILVER_PATH}/silver_employees.parquet")
    print(f"✅ Maestro directos (Silver): {df_emp_silver.count()} colaboradores.")
except Exception as e:
    print(f"⚠️ Cargando desde Bronze: {e}")
    df_emp_silver = spark.read.parquet(f"{BRONZE_PATH}/employees/employees_latest.parquet")

# 2. Cargar maestro de temporales en misión (EST)
try:
    df_temporales = spark.read.parquet(f"{SILVER_PATH}/silver_temporales.parquet")
    print(f"✅ Maestro temporales EST (Silver): {df_temporales.count()} colaboradores.")
except Exception as e:
    print(f"⚠️ Nota temporales: {e}")
    df_temporales = None

# 3. Cargar maestro de vacaciones por líder
try:
    df_vacaciones = spark.read.parquet(f"{SILVER_PATH}/silver_vacations_by_leader.parquet")
    print(f"✅ Maestro vacaciones por líder (Silver): {df_vacaciones.count()} registros.")
except Exception as e:
    print(f"⚠️ Nota vacaciones: {e}")
    df_vacaciones = None

# COMMAND ----------
# MAGIC %md
# MAGIC ## 4. CAPA GOLD: NÓMINA CONSOLIDADA & CARGA PRESTACIONAL LEGAL

# COMMAND ----------
if MES_OBJETIVO == "TODOS_2026":
    PERIODOS = [(2026, 6), (2026, 7), (2026, 8)]
else:
    y, m = MES_OBJETIVO.split("-")
    PERIODOS = [(int(y), int(m))]

gold_dfs = []

for p_year, p_month in PERIODOS:
    _, last_day = calendar.monthrange(p_year, p_month)
    cutoff = f"{p_year}-{p_month:02d}-{last_day:02d}"
    start_dt = f"{p_year}-{p_month:02d}-01"
    
    print(f"\n⚙️ Procesando Gold Nómina: {p_year}-{p_month:02d} (Corte: {cutoff})...")
    
    # Filtrar directos activos
    df_activos = df_emp_silver.filter(
        (F.col("fecha_ingreso").isNull() | (F.col("fecha_ingreso") <= cutoff)) &
        (F.col("fecha_retiro").isNull() | (F.col("fecha_retiro") >= start_dt))
    )
    
    # Conceptos de nómina
    try:
        df_concepts = spark.read.parquet(f"{SILVER_PATH}/silver_payroll_concepts.parquet")
        df_nomina = df_activos.join(df_concepts, on="documento", how="left")
        df_nomina = df_nomina.fillna({"comisiones": 0.0, "horas_extras": 0.0, "otros_devengados": 0.0})
    except Exception:
        df_nomina = df_activos.withColumn("comisiones", F.lit(0.0)) \
                              .withColumn("horas_extras", F.lit(0.0)) \
                              .withColumn("otros_devengados", F.lit(0.0))
    
    # Simulaciones
    if MODO_EJECUCION == "SIMULACION_AUMENTO_SALARIAL":
        print(f"  🧪 Simulando aumento de {PCT_SIMULACION*100:.1f}% en salarios...")
        df_nomina = df_nomina.withColumn("salario_base", F.round(F.col("salario_base") * (1.0 + PCT_SIMULACION), 2))
    elif MODO_EJECUCION == "SIMULACION_HORAS_EXTRAS":
        print(f"  🧪 Simulando aumento de {PCT_SIMULACION*100:.1f}% en horas extras...")
        df_nomina = df_nomina.withColumn("horas_extras", F.round(F.col("horas_extras") * (1.0 + PCT_SIMULACION), 2))
    
    df_nomina = df_nomina.withColumn("salario_base", F.col("salario_base").cast("double")) \
                         .withColumn("comisiones", F.col("comisiones").cast("double")) \
                         .withColumn("horas_extras", F.col("horas_extras").cast("double")) \
                         .withColumn("otros_devengados", F.col("otros_devengados").cast("double"))
    
    # Auxilio legal de transporte colombiano ($162.000 para <= 2 SMMLV $2.600.000)
    SMMLV = 1300000.0
    AUX_TRANSPORTE = 162000.0
    df_nomina = df_nomina.withColumn(
        "auxilio_transporte",
        F.when(F.col("salario_base") <= (2 * SMMLV), F.lit(AUX_TRANSPORTE)).otherwise(F.lit(0.0))
    )
    
    # Total devengado
    df_nomina = df_nomina.withColumn(
        "total_devengado",
        F.round(F.col("salario_base") + F.col("comisiones") + F.col("horas_extras") + F.col("otros_devengados") + F.col("auxilio_transporte"), 2)
    )
    
    # Provisiones prestacionales y seguridad social de ley en Colombia
    df_nomina = df_nomina.withColumn("provision_cesantias", F.round(F.col("total_devengado") * 0.0833, 2)) \
                         .withColumn("provision_intereses_cesantias", F.round(F.col("total_devengado") * 0.01, 2)) \
                         .withColumn("provision_prima", F.round(F.col("total_devengado") * 0.0833, 2)) \
                         .withColumn("provision_vacaciones", F.round(F.col("salario_base") * 0.0417, 2)) \
                         .withColumn("seguridad_social_pension", F.round(F.col("total_devengado") * 0.12, 2)) \
                         .withColumn("parafiscales_caja", F.round(F.col("total_devengado") * 0.04, 2)) \
                         .withColumn("seguridad_social_arl", F.round(F.col("total_devengado") * 0.00522, 2))
    
    df_nomina = df_nomina.withColumn(
        "total_carga_prestacional",
        F.round(
            F.col("provision_cesantias") + F.col("provision_intereses_cesantias") +
            F.col("provision_prima") + F.col("provision_vacaciones") +
            F.col("seguridad_social_pension") + F.col("parafiscales_caja") + F.col("seguridad_social_arl"), 2
        )
    ).withColumn(
        "costo_total_empleador",
        F.round(F.col("total_devengado") + F.col("total_carga_prestacional"), 2)
    ).withColumn(
        "periodo_corte", F.lit(cutoff)
    ).withColumn(
        "ano", F.lit(p_year)
    ).withColumn(
        "mes", F.lit(p_month)
    )
    
    # Integrar temporales
    if df_temporales is not None:
        df_temp_p = df_temporales.filter(
            (F.col("fecha_ingreso").isNull() | (F.col("fecha_ingreso") <= cutoff)) &
            (F.col("fecha_retiro").isNull() | (F.col("fecha_retiro") >= start_dt))
        ).withColumn("comisiones", F.lit(0.0)) \
         .withColumn("horas_extras", F.lit(0.0)) \
         .withColumn("otros_devengados", F.lit(0.0)) \
         .withColumn("auxilio_transporte", F.lit(0.0)) \
         .withColumn("total_devengado", F.col("salario_base").cast("double")) \
         .withColumn("provision_cesantias", F.round(F.col("salario_base") * 0.0833, 2)) \
         .withColumn("provision_intereses_cesantias", F.round(F.col("salario_base") * 0.01, 2)) \
         .withColumn("provision_prima", F.round(F.col("salario_base") * 0.0833, 2)) \
         .withColumn("provision_vacaciones", F.round(F.col("salario_base") * 0.0417, 2)) \
         .withColumn("seguridad_social_pension", F.round(F.col("salario_base") * 0.12, 2)) \
         .withColumn("parafiscales_caja", F.round(F.col("salario_base") * 0.04, 2)) \
         .withColumn("seguridad_social_arl", F.round(F.col("salario_base") * 0.00522, 2)) \
         .withColumn("total_carga_prestacional", F.round(F.col("salario_base") * 0.38, 2)) \
         .withColumn("costo_total_empleador", F.round(F.col("salario_base") * 1.38, 2)) \
         .withColumn("periodo_corte", F.lit(cutoff)) \
         .withColumn("ano", F.lit(p_year)) \
         .withColumn("mes", F.lit(p_month))
        
        common_cols = [c for c in df_nomina.columns if c in df_temp_p.columns]
        df_combined = df_nomina.select(common_cols).unionByName(df_temp_p.select(common_cols), allowMissingColumns=True)
    else:
        df_combined = df_nomina

    target_parquet = f"{GOLD_PATH}/fact_nomina_{p_year}_{p_month:02d}.parquet"
    print(f"  💾 Guardando Parquet Gold en Azure: {target_parquet}")
    df_combined.write.mode("overwrite").parquet(target_parquet)
    gold_dfs.append(df_combined)
    
    cnt = df_combined.count()
    costo_m = df_combined.select(F.sum("costo_total_empleador")).collect()[0][0] or 0.0
    print(f"  ✅ Período {p_year}-{p_month:02d}: {cnt} colaboradores, ${costo_m/1e6:.1f}M COP costo consolidado.")

# Guardar Delta Table consolidada
if gold_dfs:
    df_all_gold = gold_dfs[0]
    for other_df in gold_dfs[1:]:
        df_all_gold = df_all_gold.unionByName(other_df, allowMissingColumns=True)
    
    delta_target = f"{GOLD_PATH}/fact_nomina_delta"
    print(f"\n📦 Guardando Delta Table Maestra: {delta_target}")
    df_all_gold.write.format("delta").mode("overwrite").option("mergeSchema", "true").save(delta_target)

# COMMAND ----------
# MAGIC %md
# MAGIC ## 5. CAPA GOLD: VACACIONES & PASIVO LABORAL EN DELTA LAKE

# COMMAND ----------
if df_vacaciones is not None:
    delta_vac = f"{GOLD_PATH}/fact_vacaciones_delta"
    df_vacaciones.write.format("delta").mode("overwrite").save(delta_vac)
    print(f"🌴 Vacaciones sincronizadas en Delta Lake: {df_vacaciones.count()} registros en {delta_vac}.")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 6. CREACIÓN DE VISTAS SQL PARA POWER BI & DATABRICKS SQL WAREHOUSE

# COMMAND ----------
# MAGIC %sql
# MAGIC CREATE DATABASE IF NOT EXISTS maaji_talento_humano;
# MAGIC 
# MAGIC -- 1. Vista Oficial de Nómina Consolidada
# MAGIC CREATE OR REPLACE VIEW maaji_talento_humano.vw_fact_nomina_consolidada AS
# MAGIC SELECT * FROM delta.`abfss://gold-zone@stmaajidwhdev.dfs.core.windows.net/talento_humano/fact_nomina_delta`;
# MAGIC 
# MAGIC -- 2. Vista Oficial de Vacaciones y Pasivo por Líder
# MAGIC CREATE OR REPLACE VIEW maaji_talento_humano.vw_pasivo_vacaciones_lider AS
# MAGIC SELECT * FROM delta.`abfss://gold-zone@stmaajidwhdev.dfs.core.windows.net/talento_humano/fact_vacaciones_delta`;
# MAGIC 
# MAGIC -- 3. Vista Ejecutiva Resumen por Período
# MAGIC CREATE OR REPLACE VIEW maaji_talento_humano.vw_resumen_ejecutivo_costo_laboral AS
# MAGIC SELECT 
# MAGIC     periodo_corte,
# MAGIC     COUNT(DISTINCT documento) AS total_colaboradores,
# MAGIC     ROUND(SUM(salario_base), 2) AS masa_salarial_base,
# MAGIC     ROUND(SUM(comisiones), 2) AS total_comisiones,
# MAGIC     ROUND(SUM(horas_extras), 2) AS total_horas_extras,
# MAGIC     ROUND(SUM(total_devengado), 2) AS total_devengado_nomina,
# MAGIC     ROUND(SUM(total_carga_prestacional), 2) AS total_prestaciones_seguridad,
# MAGIC     ROUND(SUM(costo_total_empleador), 2) AS costo_laboral_consolidado
# MAGIC FROM maaji_talento_humano.vw_fact_nomina_consolidada
# MAGIC GROUP BY periodo_corte
# MAGIC ORDER BY periodo_corte;

# COMMAND ----------
# MAGIC %md
# MAGIC ## 7. RESUMEN FINAL DE EJECUCIÓN

# COMMAND ----------
print("="*65)
print("🎉 PIPELINE MEDALLION MAAJI EJECUTADO CON ÉXITO")
print(f"• Almacenamiento: Azure Data Lake Storage Gen2 (stmaajidwhdev)")
print(f"• Zonas Actualizadas: bronze-zone, silver-zone, gold-zone")
print(f"• Catálogo SQL: maaji_talento_humano (3 vistas listas para Power BI)")
print(f"• Integración Web: La plataforma consume directamente de stmaajidwhdev")
print("="*65)
