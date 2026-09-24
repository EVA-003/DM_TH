# -*- coding: utf-8 -*-
import os, requests

token = os.getenv('BUK_API_TOKEN', 'EMVvA6ppoVTtRdoXgqu8JSWj')
tenant = os.getenv('BUK_TENANT', 'maaji')
headers = {'auth_token': token, 'Accept': 'application/json'}
base_url = f"https://{tenant}.buk.co/api/v1/colombia"

job_id = 17635

candidates = [
    f"payrolls?job_id={job_id}",
    f"payrolls/{job_id}",
    f"jobs/{job_id}/payrolls",
    f"jobs/{job_id}/items",
    f"jobs/{job_id}/settlement",
    f"jobs/{job_id}/remunerations",
    f"employees/3289/payrolls",
    f"employees/3289/settlements",
    f"employees/3289/settlement"
]

for ep in candidates:
    url = f"{base_url}/{ep}"
    r = requests.get(url, headers=headers, timeout=10)
    print(f"[{r.status_code}] GET {ep}")
    if r.status_code == 200:
        data = r.json()
        print("   Data:", data)
