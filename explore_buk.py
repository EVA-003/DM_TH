# -*- coding: utf-8 -*-
import os
import sys
import json
import requests

token = os.getenv('BUK_API_TOKEN', 'EMVvA6ppoVTtRdoXgqu8JSWj')
tenant = os.getenv('BUK_TENANT', 'maaji')
base_url = f"https://{tenant}.buk.co/api/v1/colombia"
headers = {'auth_token': token, 'Accept': 'application/json'}

def test_endpoint(ep, params=None):
    clean_ep = ep.strip('/')
    url = f"{base_url}/{clean_ep}"
    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        print(f"[{r.status_code}] GET {ep}")
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict):
                keys = list(data.keys())
                items = data.get('data', data.get(clean_ep.split('?')[0].split('/')[0], []))
                if isinstance(items, list) and len(items) > 0:
                    print(f"   Items count: {len(items)}, Keys: {list(items[0].keys()) if isinstance(items[0], dict) else type(items[0])}")
                    return items
                print(f"   Dict keys: {keys}")
                return data
            elif isinstance(data, list):
                print(f"   List count: {len(data)}, Keys: {list(data[0].keys()) if data and isinstance(data[0], dict) else type(data[0])}")
                return data
        else:
            print(f"   Response: {r.text[:250]}")
    except Exception as e:
        print(f"   Exception: {e}")
    return None

if __name__ == '__main__':
    print("=== 1. CURRENT_JOB EXPLORATION ===")
    emp_data = test_endpoint('employees', {'page_size': 5, 'page': 1})
    if emp_data and len(emp_data) > 0:
        for emp in emp_data[:2]:
            cj = emp.get('current_job', {})
            print(f"Employee ID {emp.get('id')} - current_job:")
            if cj:
                for k, v in cj.items():
                    val_str = str(v if not isinstance(v, (dict, list)) else list(v.keys()) if isinstance(v, dict) else len(v))
                    print(f"    {k}: {type(v).__name__} = {val_str}")

    print("\n=== 2. PROCESS PERIODS ===")
    periods = test_endpoint('process_periods')
    if periods and isinstance(periods, list) and len(periods) > 0:
        print("Sample process period keys:", list(periods[0].keys()) if isinstance(periods[0], dict) else periods[0])
        print("Sample process period:", periods[0])

    print("\n=== 3. ACTIVE EMPLOYEES ===")
    active_emp = test_endpoint('employees/active', {'date': '2026-07-31', 'page_size': 5})

    print("\n=== 4. ORGANIZATIONAL ENTITIES ===")
    companies = test_endpoint('companies')
    areas = test_endpoint('areas')
    roles = test_endpoint('roles')
    jobs = test_endpoint('jobs')

    print("\n=== 5. PAYROLL / SETTLEMENTS / ITEMS ===")
    test_endpoint('settlements')
    test_endpoint('payroll_items')
    test_endpoint('custom_attributes')
    test_endpoint('items')
