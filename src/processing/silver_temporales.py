import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SilverTemporalesProcessor")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
BRONZE_DIR = BASE_DIR / "data" / "bronze" / "temporales"
SILVER_DIR = BASE_DIR / "data" / "silver"
SILVER_DIR.mkdir(parents=True, exist_ok=True)

class SilverTemporalesProcessor:
    def __init__(self):
        self.bronze_file = BRONZE_DIR / "maestra_personal_temporal.xlsx"
        self.silver_file = SILVER_DIR / "silver_temporales.parquet"

    def process(self) -> pd.DataFrame:
        logger.info("Iniciando procesamiento de Maestra de Personal Temporal...")
        if not self.bronze_file.exists():
            raise FileNotFoundError(f"No se encontró el archivo: {self.bronze_file}")

        # 1. Leer hoja MAS
        df_mas = pd.read_excel(self.bronze_file, sheet_name="Temporales MAS ", header=1)
        df_mas["empresa_nombre"] = "MAS S.A.S BIC"
        
        # 2. Leer hoja ARTMODE
        df_art = pd.read_excel(self.bronze_file, sheet_name="Temporales ARTMODE", header=1)
        df_art["empresa_nombre"] = "ART MODE S.A.S BIC"

        # 3. Normalizar columnas MAS
        # ['CEDULA', 'NOMBRES', 'GENERO', 'ESTADO', 'SALARIO ', 'Turno', 'F de ingreso ', 'F de retiro', 'CARGO', 'AREA/TIENDA', 'LIDER ', 'CECO ', 'CELULAR']
        df_mas_clean = pd.DataFrame({
            "documento": df_mas["CEDULA"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip(),
            "nombre_completo": df_mas["NOMBRES"].astype(str).str.strip().str.title(),
            "genero": df_mas["GENERO"].astype(str).str.strip(),
            "estado": df_mas["ESTADO"].astype(str).str.strip().str.upper(),
            "salario_base": pd.to_numeric(df_mas["SALARIO "], errors="coerce").fillna(0.0),
            "fecha_ingreso": pd.to_datetime(df_mas["F de ingreso "], errors="coerce").dt.strftime("%Y-%m-%d"),
            "fecha_retiro": pd.to_datetime(df_mas["F de retiro"], errors="coerce").dt.strftime("%Y-%m-%d"),
            "cargo_nombre": df_mas["CARGO"].astype(str).str.strip().str.title(),
            "area_nombre": df_mas["AREA/TIENDA"].astype(str).str.strip(),
            "lider_supervisor": df_mas["LIDER "].astype(str).str.strip().str.title(),
            "centro_costos": df_mas["CECO "].astype(str).str.strip(),
            "empresa_nombre": df_mas["empresa_nombre"],
            "tipo_vinculacion": "Empresa de Servicios Temporales (EST)"
        })

        # 4. Normalizar columnas ARTMODE
        # ['CEDULA ', 'NOMBRES', 'GENERO', 'ESTADO ', 'SALARIOS', 'F. INGRESO', 'F. RETIRO', 'CARGO', 'AREA ', 'LIDER ', 'CECO ']
        col_ced = [c for c in df_art.columns if "CEDULA" in c][0]
        col_est = [c for c in df_art.columns if "ESTADO" in c][0]
        col_sal = [c for c in df_art.columns if "SALARIO" in c][0]
        col_ing = [c for c in df_art.columns if "INGRESO" in c][0]
        col_ret = [c for c in df_art.columns if "RETIRO" in c][0]
        col_car = [c for c in df_art.columns if "CARGO" in c][0]
        col_are = [c for c in df_art.columns if "AREA" in c][0]
        col_lid = [c for c in df_art.columns if "LIDER" in c][0]
        col_cec = [c for c in df_art.columns if "CECO" in c][0]

        df_art_clean = pd.DataFrame({
            "documento": df_art[col_ced].astype(str).str.replace(r"\.0$", "", regex=True).str.strip(),
            "nombre_completo": df_art["NOMBRES"].astype(str).str.strip().str.title(),
            "genero": df_art["GENERO"].astype(str).str.strip(),
            "estado": df_art[col_est].astype(str).str.strip().str.upper(),
            "salario_base": pd.to_numeric(df_art[col_sal], errors="coerce").fillna(0.0),
            "fecha_ingreso": pd.to_datetime(df_art[col_ing], errors="coerce").dt.strftime("%Y-%m-%d"),
            "fecha_retiro": pd.to_datetime(df_art[col_ret], errors="coerce").dt.strftime("%Y-%m-%d"),
            "cargo_nombre": df_art[col_car].astype(str).str.strip().str.title(),
            "area_nombre": df_art[col_are].astype(str).str.strip(),
            "lider_supervisor": df_art[col_lid].astype(str).str.strip().str.title(),
            "centro_costos": df_art[col_cec].astype(str).str.strip(),
            "empresa_nombre": df_art["empresa_nombre"],
            "tipo_vinculacion": "Empresa de Servicios Temporales (EST)"
        })

        # 5. Consolidar
        df_consolidado = pd.concat([df_mas_clean, df_art_clean], ignore_index=True)
        df_consolidado = df_consolidado[df_consolidado["documento"] != "nan"]
        df_consolidado = df_consolidado[df_consolidado["nombre_completo"] != "Nan"]

        df_consolidado.to_parquet(self.silver_file, index=False)
        logger.info(f"Silver Temporales procesado con éxito: {len(df_consolidado)} registros históricos ({len(df_consolidado[df_consolidado['estado'] == 'ACTIVO'])} activos).")
        return df_consolidado

if __name__ == "__main__":
    p = SilverTemporalesProcessor()
    df = p.process()
    print("Muestra Temporales Activos:")
    print(df[df["estado"] == "ACTIVO"][["documento", "nombre_completo", "empresa_nombre", "cargo_nombre", "area_nombre", "lider_supervisor"]].to_string())
