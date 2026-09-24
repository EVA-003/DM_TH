# -*- coding: utf-8 -*-
import os, requests, json
import pandas as pd

token = os.getenv('BUK_API_TOKEN', 'EMVvA6ppoVTtRdoXgqu8JSWj')
tenant = os.getenv('BUK_TENANT', 'maaji')
headers = {'auth_token': token, 'Accept': 'application/json'}
base_url = f"https://{tenant}.buk.co/api/v1/colombia"

print("Extrayendo muestra de colaboradores activos...")
r = requests.get(f"{base_url}/employees/active?page_size=25&page=1", headers=headers, timeout=15)
if r.status_code == 200:
    data = r.json().get('data', [])
    records = []
    for emp in data:
        cj = emp.get('current_job') or {}
        role_obj = cj.get('role') or {}
        records.append({
            'buk_id': emp.get('id'),
            'tipo_doc': emp.get('document_type'),
            'documento': emp.get('document_number'),
            'nombre_completo': emp.get('full_name'),
            'estado': emp.get('status'),
            'fecha_ingreso': emp.get('active_since'),
            'empresa_id': cj.get('company_id'),
            'area_id': cj.get('area_id'),
            'centro_costos': cj.get('cost_center'),
            'cargo_id': cj.get('role_id'),
            'cargo_nombre': role_obj.get('name') if isinstance(role_obj, dict) else '',
            'salario_base': cj.get('wage'),
            'tipo_contrato': cj.get('type_of_contract'),
            'tipo_riesgo_arl': cj.get('risk_type'),
            'eps': emp.get('health_company'),
            'fondo_pension': emp.get('pension_fund')
        })
    
    df = pd.DataFrame(records)
    print("\n--- DATAFRAME SILVER PREVIEW (Muestra de 10 empleados) ---")
    print(df[['documento', 'nombre_completo', 'cargo_nombre', 'salario_base', 'tipo_contrato', 'tipo_riesgo_arl']].head(10).to_string())
    print(f"\nTotal registros en muestra: {len(df)}")
