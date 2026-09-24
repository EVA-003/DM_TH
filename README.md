# Datamart y Plataforma de Gestión de Nómina – Maaji
### Integración Buk Colombia API & Arquitectura Medallion (Databricks)

Plataforma empresarial para la automatización, auditoría y análisis de la gestión de nómina mensual en Maaji, reemplazando procesos manuales en hojas de cálculo por un pipeline moderno de ingeniería de datos.

---

## 🚀 Arquitectura del Proyecto

```text
DM_TH/
├── config/
│   ├── settings.py              # Configuración general y variables de entorno
│   └── mapping_rules.py         # Tarifas ARL, provisiones prestacionales y MOD/MOI
├── src/
│   ├── ingestion/               # CAPA BRONZE (Buk Client & Ingesta Cruda)
│   │   ├── buk_client.py
│   │   └── bronze_pipeline.py
│   ├── processing/              # CAPA SILVER (Limpieza, Antigüedad, Normalización)
│   │   └── silver_employees.py
│   ├── datamart/                # CAPA GOLD (Datamart Dimensional de Hechos)
│   │   └── gold_fact_nomina.py
│   └── exports/                 # MOTOR DE EXPORTACIÓN OFICIAL EXCEL
│       └── report_generator.py
├── data/                        # STORAGE LOCAL (Ignorado en Git)
│   ├── bronze/                  # Datos crudos (Parquet + JSON versionado)
│   ├── silver/                  # Tablas normalizadas (Parquet)
│   ├── gold/                    # Datamart mensual (Parquet)
│   └── outputs/                 # Informes mensuales oficiales generados (.xlsx)
├── app/
│   └── app.py                   # Plataforma Web y Dashboard Interactivo (Streamlit)
├── notebooks/                   # Notebooks compatibles con Databricks
│   ├── 01_Bronze_Ingestion.ipynb
│   ├── 02_Silver_Processing.ipynb
│   └── 03_Gold_Datamart_Export.ipynb
├── requirements.txt
└── test_buk_connection.py
```

---

## 💻 ¿Cómo Ejecutar la Plataforma?

### 1. Iniciar la Plataforma Web / Dashboard
Para abrir la interfaz interactiva con métricas, gráficos y descarga del informe oficial en 1 clic:
```bash
streamlit run app/app.py
```

### 2. Ejecutar el Pipeline Completo por Consola
```bash
# Ingesta Bronze
python -m src.ingestion.bronze_pipeline

# Procesamiento Silver
python -m src.processing.silver_employees

# Datamart Gold (Mes deseado)
python -m src.datamart.gold_fact_nomina

# Generación del Informe Oficial Excel
python -m src.exports.report_generator
```

---

## 🔒 Seguridad de Credenciales
Las credenciales nunca se guardan en el código fuente. Se configuran mediante variables de entorno:
```powershell
$env:BUK_TENANT = "maaji"
$env:BUK_API_TOKEN = "tu_api_key_aqui"
```
En Databricks se utilizan Secret Scopes (`dbutils.secrets.get`).
