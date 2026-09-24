# -*- coding: utf-8 -*-
import os
import requests

token = os.getenv('BUK_API_TOKEN', 'EMVvA6ppoVTtRdoXgqu8JSWj')
tenant = os.getenv('BUK_TENANT', 'maaji')
headers = {'auth_token': token, 'Accept': 'application/json'}

urls = [
    f"https://{tenant}.buk.co/apidocs",
    f"https://{tenant}.buk.co/api/v1/swagger.json",
    f"https://{tenant}.buk.co/api/v1/openapi.json",
    f"https://{tenant}.buk.co/api/v1/colombia/swagger.json",
    f"https://{tenant}.buk.co/api/v1/colombia/docs",
    f"https://{tenant}.buk.co/api/v1/colombia/custom_attributes",
    f"https://{tenant}.buk.co/api/v1/colombia/employee_custom_attributes",
    f"https://{tenant}.buk.co/api/v1/colombia/assignments",
    f"https://{tenant}.buk.co/api/v1/colombia/item_assignments",
    f"https://{tenant}.buk.co/api/v1/colombia/remunerations",
    f"https://{tenant}.buk.co/api/v1/colombia/payrolls",
    f"https://{tenant}.buk.co/api/v1/colombia/overtimes",
    f"https://{tenant}.buk.co/api/v1/colombia/hours",
    f"https://{tenant}.buk.co/api/v1/colombia/asistencia/marks",
    f"https://{tenant}.buk.co/api/v1/colombia/asistencia/shifts",
    f"https://{tenant}.buk.co/api/v1/colombia/asistencia/overtimes",
]

for u in urls:
    try:
        r = requests.get(u, headers=headers, timeout=10)
        print(f"[{r.status_code}] {u} (content-type: {r.headers.get('content-type', '')})")
    except Exception as e:
        print(f"[ERR] {u} -> {e}")
