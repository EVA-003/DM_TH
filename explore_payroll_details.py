# -*- coding: utf-8 -*-
import os
import requests

token = os.getenv('BUK_API_TOKEN', 'EMVvA6ppoVTtRdoXgqu8JSWj')
tenant = os.getenv('BUK_TENANT', 'maaji')
base_url = f"https://{tenant}.buk.co/api/v1/colombia"
headers = {'auth_token': token, 'Accept': 'application/json'}

def check_ep(ep, params=None):
    url = f"{base_url}/{ep.strip('/')}"
    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        print(f"[{r.status_code}] GET {ep}")
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict):
                print("   Keys:", list(data.keys()))
                sub = data.get('data', data)
                if isinstance(sub, list) and len(sub) > 0:
                    print("   First item sample:", list(sub[0].keys()) if isinstance(sub[0], dict) else sub[0])
                elif isinstance(sub, dict):
                    print("   Data keys:", list(sub.keys()))
            elif isinstance(data, list) and len(data) > 0:
                print("   List sample item:", list(data[0].keys()) if isinstance(data[0], dict) else data[0])
            return data
    except Exception as e:
        print("   Error:", e)
    return None

# Test with employee ID 3066 or active employee
check_ep("employees/3066")
check_ep("employees/3066/items")
check_ep("employees/3066/plans")
check_ep("employees/3066/custom_attributes")
check_ep("employees/3066/current_job")
check_ep("process_periods/530")
check_ep("process_periods/530/settlements")
check_ep("process_periods/530/employees")
check_ep("process_periods/530/items")
