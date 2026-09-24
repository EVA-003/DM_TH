# -*- coding: utf-8 -*-
import os, requests

token = os.getenv('BUK_API_TOKEN', 'EMVvA6ppoVTtRdoXgqu8JSWj')
tenant = os.getenv('BUK_TENANT', 'maaji')
headers = {'auth_token': token, 'Accept': 'application/json'}
base_url = f"https://{tenant}.buk.co/api/v1/colombia"

endpoints = [
    "items/516/assigned_employees",
    "items/516/employees",
    "items/516/item_assignments",
    "items/516/assignments",
    "items/516/values",
    "employees/3066/item_assignments",
    "employees/3066/assigned_items",
    "employees/3066/items",
    "assigned_items",
    "item_assignments"
]

for ep in endpoints:
    url = f"{base_url}/{ep}"
    r = requests.get(url, headers=headers, timeout=10)
    print(f"[{r.status_code}] GET {ep}")
    if r.status_code == 200:
        print("   Response:", r.json())
