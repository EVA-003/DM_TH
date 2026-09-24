# -*- coding: utf-8 -*-
import os, requests

token = os.getenv('BUK_API_TOKEN', 'EMVvA6ppoVTtRdoXgqu8JSWj')
tenant = os.getenv('BUK_TENANT', 'maaji')
base_url = f"https://{tenant}.buk.co/api/v1/colombia"
headers = {'auth_token': token, 'Accept': 'application/json'}

candidate_endpoints = [
    'locations', 'cost_centers', 'departments', 'branches',
    'absences', 'vacations', 'licenses', 'disabilities', 'leaves',
    'benefits', 'training', 'evaluations',
    'payslips', 'payroll_slips', 'receipts', 'liquidations',
    'currencies', 'banks', 'afps', 'isapres', 'epss',
    'surveys', 'workflows'
]

print("=== PROBING ADDITIONAL BUK ENDPOINTS ===")
for ep in candidate_endpoints:
    url = f"{base_url}/{ep}"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            items = data.get('data', data) if isinstance(data, dict) else data
            count = len(items) if isinstance(items, list) else 'dict'
            sample_keys = list(items[0].keys()) if isinstance(items, list) and len(items) > 0 and isinstance(items[0], dict) else ''
            print(f"[200 OK] {ep:<18} -> Count: {count:<4} Keys: {sample_keys}")
        elif r.status_code != 404:
            print(f"[{r.status_code}] {ep}")
    except Exception as e:
        print(f"[ERR] {ep}: {e}")
