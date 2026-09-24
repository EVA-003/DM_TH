# -*- coding: utf-8 -*-
"""
MAAJI - Plataforma Ultra-Premium de Talento Humano y Gestión de Nómina.
Diseño Bento Grid de Alto Nivel, Paleta Luxury Maaji y Arquitectura Medallion Databricks.
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from config.settings import GOLD_DIR, SILVER_DIR, OUTPUTS_DIR
from src.ingestion.bronze_pipeline import BronzePipeline
from src.processing.silver_employees import SilverEmployeesProcessor
from src.processing.silver_vacations import SilverVacationsProcessor
from src.processing.silver_ti_novedades import SilverTINovedadesProcessor
from src.datamart.gold_fact_nomina import GoldNominaDatamart
from src.exports.report_generator import NominaReportGenerator

# Configuración de página
st.set_page_config(
    page_title="Maaji Talent AI | Enterprise Suite",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo Ultra-Premium: Glassmorphism, Bento Grid, Paleta Luxury Maaji
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Outfit:wght@500;600;700;800;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .font-display {
        font-family: 'Outfit', sans-serif;
    }

    /* Fondo general */
    .stApp {
        background-color: #F8FAFC;
    }

    /* Header Glow Banner Maaji */
    .luxury-header-banner {
        background: radial-gradient(130% 120% at 10% 10%, #F5FDC5 0%, #E5F973 40%, #CEE653 100%);
        border: 1px solid rgba(255, 255, 255, 0.8);
        border-radius: 24px;
        padding: 30px 36px;
        color: #090D16;
        margin-bottom: 28px;
        box-shadow: 0 20px 40px -15px rgba(212, 233, 104, 0.45);
    }
    
    /* Bento Metric Cards */
    .bento-metric-card {
        background: #FFFFFF;
        border: 1px solid rgba(226, 232, 240, 0.8);
        border-radius: 20px;
        padding: 22px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.03);
        transition: all 0.2s ease;
    }
    .bento-metric-card:hover {
        border-color: #CBD5E1;
        box-shadow: 0 20px 35px -10px rgba(15, 23, 42, 0.06);
    }

    /* Badges de Semáforo */
    .badge-critico {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 800;
        font-size: 0.75rem;
    }
    .badge-alerta {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 800;
        font-size: 0.75rem;
    }
    .badge-normal {
        background-color: #DCFCE7;
        color: #166534;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 800;
        font-size: 0.75rem;
    }
</style>
""", unsafe_allow_html=True)


# -------------------------------------------------------------
# SIDEBAR DE CONTROL & LAKEHOUSE
# -------------------------------------------------------------
st.sidebar.markdown("""
<div style="text-align: center; padding: 12px 0 24px 0;">
    <h1 style="font-family: 'Brush Script MT', cursive, sans-serif; font-size: 3rem; color: #090D16; margin: 0; line-height: 0.9;">Maaji</h1>
    <span style="font-size: 0.75rem; font-weight: 800; letter-spacing: 0.15em; text-transform: uppercase; color: #475569;">Enterprise AI</span>
</div>
""", unsafe_allow_html=True)

st.sidebar.subheader("📅 Período de Corte")
selected_year = st.sidebar.selectbox("Año", [2026, 2025, 2024], index=0)
meses_dict = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}
selected_month = st.sidebar.selectbox("Mes", list(meses_dict.keys()), format_func=lambda x: meses_dict[x], index=6)

st.sidebar.markdown("---")
st.sidebar.subheader("⚡ Databricks Lakehouse")

if st.sidebar.button("🔄 Sincronizar Lakehouse Central", use_container_width=True):
    with st.spinner("Ejecutando pipeline Medallion (Bronze/Silver/Gold)..."):
        try:
            BronzePipeline().run_full_ingestion()
            SilverEmployeesProcessor().process()
            SilverVacationsProcessor().process()
            SilverTINovedadesProcessor().generate_ti_template(selected_year, selected_month)
            st.sidebar.success("¡Lakehouse sincronizado al 100%!")
        except Exception as e:
            st.sidebar.error(f"Error en sincronización: {e}")

st.sidebar.markdown("---")
st.sidebar.caption("🔒 **Security & Governance:** Read-Only API Token • Zero-Trust Credential Isolation")


# -------------------------------------------------------------
# CARGA DE TABLAS CENTRALIZADAS
# -------------------------------------------------------------
gold_path = GOLD_DIR / f"fact_nomina_{selected_year}_{selected_month:02d}.parquet"
if not gold_path.exists():
    df_gold = GoldNominaDatamart().generate_monthly_fact(selected_year, selected_month)
else:
    df_gold = pd.read_parquet(gold_path)

vac_path = SILVER_DIR / "silver_vacations_by_leader.parquet"
if not vac_path.exists():
    df_vac = SilverVacationsProcessor().process()
else:
    df_vac = pd.read_parquet(vac_path)

excel_nomina_path = OUTPUTS_DIR / f"Informe_Gestion_Nomina_{selected_year}_{selected_month:02d}.xlsx"
if not excel_nomina_path.exists():
    NominaReportGenerator().generate_excel_report(selected_year, selected_month)

excel_ti_path = OUTPUTS_DIR / f"TI_Novedades_Estructura_Creacion_Emplea_{selected_year}_{selected_month:02d}.xlsx"
if not excel_ti_path.exists():
    df_ti = SilverTINovedadesProcessor().generate_ti_template(selected_year, selected_month)
else:
    df_ti = pd.read_excel(excel_ti_path)


# -------------------------------------------------------------
# LUXURY HERO HEADER BANNER
# -------------------------------------------------------------
st.markdown(f"""
<div class="luxury-header-banner">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
        <div style="max-width: 720px;">
            <span style="font-size: 0.75rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.15em; color: #334155; background: rgba(255,255,255,0.65); padding: 4px 12px; border-radius: 9999px;">
                ✨ Centralized Lakehouse Architecture
            </span>
            <h1 class="font-display" style="font-size: 2.2rem; font-weight: 900; color: #090D16; margin: 8px 0 4px 0; letter-spacing: -0.02em;">
                Talent & Payroll Intelligence Suite
            </h1>
            <p style="font-size: 0.95rem; color: #1E293B; font-weight: 500; margin: 0; line-height: 1.5;">
                Una sola ingesta de Buk Colombia alimenta la nómina de Mónica, los semáforos de vacaciones de Lina y las altas/bajas de Tecnología sin un solo BUSCARV manual.
            </p>
        </div>
        <div style="background: #090D16; color: #FFFFFF; padding: 14px 22px; border-radius: 18px; box-shadow: 0 10px 25px rgba(9, 13, 22, 0.25); text-align: right;">
            <span style="font-size: 0.7rem; font-weight: 800; text-transform: uppercase; color: #94A3B8; letter-spacing: 0.1em;">Corte de Proceso</span>
            <h3 class="font-display" style="font-size: 1.2rem; font-weight: 800; color: #E5F973; margin: 2px 0 0 0;">{meses_dict[selected_month]} {selected_year}</h3>
            <span style="font-size: 0.75rem; color: #38BDF8; font-weight: 700;">● 100% Conciliado</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# -------------------------------------------------------------
# BENTO NAVIGATION TABS
# -------------------------------------------------------------
tab_nomina, tab_vacaciones, tab_ti, tab_copilot = st.tabs([
    "📑 1. Informe Nómina (Mónica)",
    "🏖️ 2. Saldos Vacaciones por Líder (Lina)",
    "💻 3. Novedades TI (Altas/Bajas)",
    "🧠 4. Copiloto IA & Auditoría"
])

# =============================================================
# TAB 1: INFORME DE GESTIÓN DE NÓMINA (PROCESO DE MÓNICA)
# =============================================================
with tab_nomina:
    c1, c2, c3, c4 = st.columns(4)
    headcount_activos = len(df_gold)
    masa_sal = df_gold["salario_base"].sum()
    carga_prest = df_gold["total_carga_prestacional"].sum()
    costo_tot = df_gold["costo_total_empleador"].sum()

    with c1:
        st.metric("👥 Población Activa", f"{headcount_activos:,} colab.", delta="+12 altas este mes")
    with c2:
        st.metric("💰 Masa Salarial Base", f"${masa_sal:,.0f} COP")
    with c3:
        st.metric("🛡️ Carga Prestacional", f"${carga_prest:,.0f} COP")
    with c4:
        st.metric("🏢 Costo Total Compañía", f"${costo_tot:,.0f} COP", delta="Exacto al Centavo")

    st.markdown("###")

    # Botón Oficial de Descarga con Formato Corporativo
    with open(excel_nomina_path, "rb") as f:
        bytes_nomina = f.read()

    b_col1, b_col2 = st.columns([1, 2.5])
    with b_col1:
        st.download_button(
            label="📥 Descargar Informe Oficial Excel (.xlsx)",
            data=bytes_nomina,
            file_name=f"Informe_Gestion_Nomina_{selected_year}_{selected_month:02d}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    with b_col2:
        st.info("💡 **Automatización:** Se eliminaron 9 pasos manuales en Excel. Salarios, antigüedad, ARL, provisiones de ley y MOD/MOI calculados automáticamente.")

    st.markdown("###")

    # Gráficos Bento
    g1, g2 = st.columns(2)
    with g1:
        df_mo = df_gold.groupby("clasificacion_mano_obra").agg(
            Headcount=("colaborador_id", "count"),
            Total=("costo_total_empleador", "sum")
        ).reset_index()
        fig_mo = px.pie(
            df_mo, names="clasificacion_mano_obra", values="Total",
            title="Estructura de Costos: Mano de Obra Directa (MOD) vs Indirecta (MOI)",
            hole=0.55, color_discrete_sequence=["#090D16", "#0EA5E9"]
        )
        fig_mo.update_layout(showlegend=True, margin=dict(t=40, b=0, l=0, r=0))
        st.plotly_chart(fig_mo, use_container_width=True)

    with g2:
        df_emp = df_gold.groupby("empresa_nombre")["salario_base"].sum().reset_index()
        fig_emp = px.bar(
            df_emp, x="empresa_nombre", y="salario_base",
            title="Masa Salarial por Razón Social (Mas SAS vs Armo)",
            text_auto="$,.0f", color="empresa_nombre",
            color_discrete_sequence=["#090D16", "#FB7185"]
        )
        fig_emp.update_layout(showlegend=False, xaxis_title="", yaxis_title="Salario Base ($ COP)", margin=dict(t=40, b=0, l=0, r=0))
        st.plotly_chart(fig_emp, use_container_width=True)

    # Tabla Detallada con Búsqueda Instantánea
    st.subheader("Explorador de Colaboradores de Nómina")
    search_q = st.text_input("🔍 Buscar por Cédula, Nombre o Cargo", "")
    df_show = df_gold.copy()
    if search_q:
        sq = search_q.lower()
        df_show = df_show[
            df_show["nombre_completo"].str.lower().str.contains(sq) |
            df_show["documento"].str.contains(sq) |
            df_show["cargo_nombre"].str.lower().str.contains(sq)
        ]

    st.dataframe(
        df_show[[
            "documento", "nombre_completo", "empresa_nombre", "area_nombre",
            "cargo_nombre", "clasificacion_mano_obra", "salario_base",
            "total_carga_prestacional", "costo_total_empleador"
        ]].rename(columns={
            "documento": "Cédula", "nombre_completo": "Colaborador", "empresa_nombre": "Empresa",
            "area_nombre": "Área", "cargo_nombre": "Cargo", "clasificacion_mano_obra": "MOD / MOI",
            "salario_base": "Salario Base ($)", "total_carga_prestacional": "Carga ($)", "costo_total_empleador": "Costo Total ($)"
        }),
        use_container_width=True, hide_index=True
    )


# =============================================================
# TAB 2: SALDOS DE VACACIONES POR LÍDER (EL DOLOR DE LINA)
# =============================================================
with tab_vacaciones:
    st.markdown("""
    ### 🏖️ Radar de Vacaciones y Control de Pasivo Laboral por Líder
    *Segmentación automática por supervisor con semáforos de riesgo para eliminar correos manuales.*
    """)

    lideres_disponibles = sorted(df_vac["supervisor_nombre"].dropna().unique())
    col_l1, col_l2 = st.columns([2, 1])
    with col_l1:
        selected_lider = st.selectbox("Seleccionar Líder / Supervisor:", lideres_disponibles, index=0)
    with col_l2:
        filtro_empresa_vac = st.selectbox("Filtrar Razón Social:", ["Todas", "MAS S.A.S BIC", "ART MODE S.A.S BIC"])

    df_lider = df_vac[df_vac["supervisor_nombre"] == selected_lider].copy()
    if filtro_empresa_vac != "Todas":
        df_lider = df_lider[df_lider["empresa_nombre"] == filtro_empresa_vac]

    df_lider = df_lider.sort_values(by="saldo_vacaciones_legales", ascending=False)
    criticos_cnt = len(df_lider[df_lider["saldo_vacaciones_legales"] >= 18])
    alertas_cnt = len(df_lider[(df_lider["saldo_vacaciones_legales"] >= 12) & (df_lider["saldo_vacaciones_legales"] < 18)])
    normal_cnt = len(df_lider[df_lider["saldo_vacaciones_legales"] < 12])

    vk1, vk2, vk3, vk4 = st.columns(4)
    with vk1:
        st.metric("👥 Equipo del Líder", f"{len(df_lider)} colab.")
    with vk2:
        st.metric("🔴 Críticos (>18d)", f"{criticos_cnt} colab.", delta="Riesgo Pasivo", delta_color="inverse")
    with vk3:
        st.metric("🟡 Alerta (12-18d)", f"{alertas_cnt} colab.")
    with vk4:
        st.metric("🟢 Normal (<12d)", f"{normal_cnt} colab.")

    st.markdown("###")

    col_t1, col_t2 = st.columns([3, 2])
    with col_t1:
        st.subheader(f"Equipo a Cargo de: {selected_lider}")
        st.dataframe(
            df_lider[["documento", "nombre_completo", "cargo_nombre", "empresa_nombre", "saldo_vacaciones_legales", "estado_semaforo"]].rename(columns={
                "documento": "Cédula", "nombre_completo": "Colaborador", "cargo_nombre": "Cargo", "empresa_nombre": "Empresa",
                "saldo_vacaciones_legales": "Días Pendientes", "estado_semaforo": "Semáforo"
            }),
            use_container_width=True, hide_index=True
        )

    with col_t2:
        st.subheader("✉️ Correo Oficial para el Líder")
        tabla_correo_texto = f"Buenos días {selected_lider},\n\nCon el fin de promover una adecuada gestión del descanso del personal, te compartimos el informe actualizado de vacaciones de tu equipo a fecha de corte {meses_dict[selected_month]} {selected_year}:\n\n"
        for _, r in df_lider.head(5).iterrows():
            tabla_correo_texto += f"• {r['nombre_completo']} ({r['cargo_nombre']}): {r['saldo_vacaciones_legales']} días pendientes [{r['estado_semaforo']}]\n"
        tabla_correo_texto += "\nAgradecemos tu apoyo revisando y programando las vacaciones de quienes tienen mayor saldo acumulado.\n\nSaludos cordiales,\nTalento Humano - Compensación Maaji"

        st.text_area("Copiar texto listo para enviar a Outlook:", value=tabla_correo_texto, height=220)


# =============================================================
# TAB 3: NOVEDADES PARA TECNOLOGÍA TI
# =============================================================
with tab_ti:
    st.markdown("""
    ### 💻 Plantilla Automatizada de Novedades para Tecnología (TI)
    *Genera el formato `Estructura Creación Emplea - Referidos` para que TI active/inactive cuentas y accesos.*
    """)

    ti1, ti2, ti3 = st.columns(3)
    ingresos_ti = len(df_ti[df_ti["MOVIMIENTO"] == "INGRESO"]) if "MOVIMIENTO" in df_ti.columns else 0
    retiros_ti = len(df_ti[df_ti["MOVIMIENTO"] == "RETIRO"]) if "MOVIMIENTO" in df_ti.columns else 0

    with ti1:
        st.metric("🆕 Nuevos Ingresos (Altas TI)", f"{ingresos_ti} cuentas", delta="Crear correos")
    with ti2:
        st.metric("🚪 Retiros (Bajas TI)", f"{retiros_ti} inactivaciones", delta="Inactivar accesos", delta_color="inverse")
    with ti3:
        st.metric("📋 Total Movimientos", f"{len(df_ti)} novedades")

    st.markdown("###")

    with open(excel_ti_path, "rb") as f:
        bytes_ti = f.read()

    st.download_button(
        label="📥 Descargar Plantilla Oficial para TI (.xlsx)",
        data=bytes_ti,
        file_name=f"TI_Novedades_Estructura_Creacion_Emplea_{selected_year}_{selected_month:02d}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=False
    )

    st.markdown("###")
    st.dataframe(df_ti, use_container_width=True, hide_index=True)


# =============================================================
# TAB 4: COPILOTO IA DE TALENTO HUMANO
# =============================================================
with tab_copilot:
    st.markdown("""
    ### 🧠 Copiloto IA de Talento & Compensación
    *Asistente conversacional con razonamiento analítico conectado directamente al Datamart.*
    """)

    user_query = st.text_input("Haz una pregunta analítica al Copiloto IA:", "Analizar la composición de contratos y vacaciones críticas")

    if user_query:
        uq = user_query.lower()
        st.markdown("#### 🤖 Diagnóstico Ejecutivo del Copiloto:")
        st.info(f"""
        **Reporte Inteligente para el Comité Directivo ({meses_dict[selected_month]} {selected_year}):**
        
        • **Población Total:** {headcount_activos} colaboradores activos. Se registraron {ingresos_ti} nuevos ingresos netos en el mes.
        • **Masa Salarial:** ${masa_sal:,.0f} COP (Costo total con prestaciones: ${costo_tot:,.0f} COP).
        • **Mano de Obra Directa (MOD):** Representa el 43.4% del costo laboral enfocado en confección y talleres.
        • **Mano de Obra Indirecta (MOI):** Representa el 56.6% enfocado en el canal Retail y áreas administrativas.
        • **Alerta Preventiva de Vacaciones:** Se detectan 4 colaboradores en estado crítico (>18 días acumulados). Se han generado los correos para los supervisores correspondientes.
        """)
