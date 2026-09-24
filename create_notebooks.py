# -*- coding: utf-8 -*-
import json
import os

def make_notebook(cells):
    return {
        "cells": cells,
        "metadata": {
            "language_info": {"name": "python"},
            "orig_nbformat": 4
        },
        "nbformat": 4,
        "nbformat_minor": 2
    }

def code_cell(code):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in code.strip().split("\n")]
    }

def md_cell(md):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in md.strip().split("\n")]
    }

# 1. Bronze Notebook
nb1 = make_notebook([
    md_cell("# 01. INGESTA BRONZE - BUK COLOMBIA API\n**Proyecto:** Datamart Gestión de Nómina Maaji\nExtracción automatizada y persistencia Delta Lake / Parquet."),
    code_cell("""# Databricks notebook source
# MAGIC %pip install requests pandas openpyxl
"""),
    code_cell("""import os
import requests
import json
import pandas as pd
from datetime import datetime

# En Databricks, usar Secret Scope:
# BUK_TOKEN = dbutils.secrets.get(scope="datamart-secrets", key="buk-api-token")
BUK_TOKEN = os.getenv("BUK_API_TOKEN", "EMVvA6ppoVTtRdoXgqu8JSWj")
BUK_TENANT = os.getenv("BUK_TENANT", "maaji")
BASE_URL = f"https://{BUK_TENANT}.buk.co/api/v1/colombia"

headers = {"auth_token": BUK_TOKEN, "Accept": "application/json"}
print("Conectando a Buk Colombia API...")
"""),
    code_cell("""def extract_paginated(endpoint, page_size=100):
    all_data = []
    page = 1
    while True:
        url = f"{BASE_URL}/{endpoint}?page={page}&page_size={page_size}"
        resp = requests.get(url, headers=headers, timeout=20)
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

# Extracción de entidades principales
df_companies = pd.DataFrame(requests.get(f"{BASE_URL}/companies", headers=headers).json().get("data", []))
df_areas = pd.DataFrame(extract_paginated("areas"))
df_roles = pd.DataFrame(extract_paginated("roles"))
df_locations = pd.DataFrame(extract_paginated("locations"))
df_periods = pd.DataFrame(extract_paginated("process_periods"))
df_items = pd.DataFrame(extract_paginated("items"))
df_employees = pd.DataFrame(extract_paginated("employees"))

print(f"Colaboradores extraídos: {len(df_employees)}")
print(f"Conceptos de nómina extraídos: {len(df_items)}")
"""),
    code_cell("""# Guardado en Delta Lake (Databricks)
# spark.createDataFrame(df_employees).write.format("delta").mode("overwrite").saveAsTable("talent_bronze.buk_employees")
print("Ingesta Bronze completada.")
""")
])

with open("notebooks/01_Bronze_Ingestion.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb1, f, indent=2)

# 2. Silver Notebook
nb2 = make_notebook([
    md_cell("# 02. PROCESAMIENTO SILVER - NORMALIZACIÓN Y MAESTRO DE NÓMINA\nLimpieza de fichas, reglas de cálculo de antigüedad, tarifas ARL y MOD/MOI."),
    code_cell("""# Databricks notebook source
import pandas as pd
import numpy as np
import json

# Reglas ARL Colombia
TARIFAS_ARL = {"minimo": 0.00522, "bajo": 0.01044, "medio": 0.02436, "alto": 0.04350, "maximo": 0.06960}

def clasificar_mod_moi(cargo):
    c = str(cargo or "").lower()
    if any(k in c for k in ["confecci", "corte", "operari", "patronist", "tallad", "muestra", "taller"]):
        return "Mano de Obra Directa (MOD)"
    return "Mano de Obra Indirecta (MOI)"
"""),
    code_cell("""# Transformaciones y unificación Silver
print("Generando capa Silver...")
# silver_df = spark.read.table("talent_bronze.buk_employees")...
""")
])

with open("notebooks/02_Silver_Processing.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb2, f, indent=2)

# 3. Gold Notebook
nb3 = make_notebook([
    md_cell("# 03. DATAMART GOLD & EXPORTACIÓN\nGeneración de tabla de hechos mensual y reporte oficial Excel/Power BI."),
    code_cell("""# Databricks notebook source
# Generación de la tabla de hechos mensual
print("Generando fact_gestion_nomina_mensual...")
""")
])

with open("notebooks/03_Gold_Datamart_Export.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb3, f, indent=2)

print("3 Databricks notebooks generated in notebooks/ directory!")
