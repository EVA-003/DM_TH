# -*- coding: utf-8 -*-
import os, requests

token = os.getenv('BUK_API_TOKEN', 'EMVvA6ppoVTtRdoXgqu8JSWj')
tenant = os.getenv('BUK_TENANT', 'maaji')
headers = {'auth_token': token, 'Accept': 'application/json'}

url = f"https://{tenant}.buk.co/api/v1/colombia/items?page_size=100"
r = requests.get(url, headers=headers, timeout=15)
if r.status_code == 200:
    data = r.json()
    items = data.get('data', [])
    print(f"Total items en pagina: {len(items)}")
    print("-" * 75)
    for it in sorted(items, key=lambda x: str(x.get('name') or '')):
        item_id = str(it.get('id') or '')
        item_type = str(it.get('type') or '')
        remun = str(it.get('remuneration_type') or '')
        name = str(it.get('name') or '')
        print(f"ID: {item_id:<6} | Tipo: {item_type:<15} | Remun: {remun:<12} | Nombre: {name}")
