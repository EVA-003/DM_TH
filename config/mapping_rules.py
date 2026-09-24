# -*- coding: utf-8 -*-
"""
Reglas de homologación, tarifas ARL, carga prestacional y clasificación MOD/MOI.
"""

# Tarifas oficiales ARL Colombia según clase de riesgo
TARIFAS_ARL = {
    "minimo": 0.00522,  # 0.522% (Clase I)
    "mínimo": 0.00522,
    "clase 1": 0.00522,
    "clase i": 0.00522,
    "1": 0.00522,
    "bajo": 0.01044,    # 1.044% (Clase II)
    "clase 2": 0.01044,
    "clase ii": 0.01044,
    "2": 0.01044,
    "medio": 0.02436,   # 2.436% (Clase III)
    "clase 3": 0.02436,
    "clase iii": 0.02436,
    "3": 0.02436,
    "alto": 0.04350,    # 4.350% (Clase IV)
    "clase 4": 0.04350,
    "clase iv": 0.04350,
    "4": 0.04350,
    "maximo": 0.06960,  # 6.960% (Clase V)
    "máximo": 0.06960,
    "clase 5": 0.06960,
    "clase v": 0.06960,
    "5": 0.06960
}

# Factor de Carga Prestacional y Seguridad Social estándar
PORCENTAJES_PRESTACIONALES = {
    "cesantias": 0.08333,       # 8.33%
    "intereses_cesantias": 0.01,# 1.00% mensual (12% anual)
    "prima_servicios": 0.08333, # 8.33%
    "vacaciones": 0.04167,      # 4.17%
    "pension_empleador": 0.12,  # 12.00%
    "caja_compensacion": 0.04,  # 4.00%
}

def clasificar_mod_moi(cargo: str, area: str = "", centro_costos: str = "") -> str:
    """
    Clasifica a un colaborador como Mano de Obra Directa (MOD) o Indirecta (MOI).
    MOD: Confección, corte, operarios de producción, técnicos de confección, muestras, taller.
    MOI: Administrativos, comercial, marketing, retail, tecnología, gerencia, logística indirecta.
    """
    cargo_clean = (cargo or "").lower()
    area_clean = (area or "").lower()
    cc_clean = (centro_costos or "").upper()

    mod_keywords = [
        "confecci", "costura", "operari", "corte", "patronist", "tallad",
        "estampad", "muestra", "trazo", "maquinista", "filetead", "plancha",
        "rematad", "revisad", "taller", "producci"
    ]
    
    if any(k in cargo_clean for k in mod_keywords) or any(k in area_clean for k in ["planta", "taller", "corte", "confeccion"]):
        return "Mano de Obra Directa (MOD)"
    return "Mano de Obra Indirecta (MOI)"
