# -*- coding: utf-8 -*-
import os, requests

token = os.getenv('BUK_API_TOKEN', 'EMVvA6ppoVTtRdoXgqu8JSWj')
tenant = os.getenv('BUK_TENANT', 'maaji')
headers = {'auth_token': token, 'Accept': 'application/json'}

all_items = []
page = 1
while True:
    url = f"https://{tenant}.buk.co/api/v1/colombia/items?page={page}&page_size=100"
    r = requests.get(url, headers=headers, timeout=15)
    if r.status_code != 200:
        break
    data = r.json()
    items = data.get('data', [])
    if not items:
        break
    all_items.extend(items)
    if not data.get('pagination', {}).get('next'):
        break
    page += 1

print(f"Total conceptos / items configurados en Buk: {len(all_items)}")
print("\n--- CONCEPTOS RELACIONADOS CON COMISIONES, BONOS Y HORAS EXTRAS ---")
for it in sorted(all_items, key=lambda x: str(x.get('name') or '')):
    name = str(it.get('name') or '')
    if any(w in name.lower() for w in ['comisi', 'extra', 'recargo', 'bono', 'dominical', 'festivo']):
        item_id = str(it.get('id') or '')
        item_type = str(it.get('type') or '')
        remun = str(it.get('remuneration_type') or '')
        code = str(it.get('code') or '')
        print(f"ID: {item_id:<6} | Código: {code:<10} | Tipo: {item_type:<14} | Nombre: {name}")
