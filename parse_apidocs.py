# -*- coding: utf-8 -*-
import requests, re

r = requests.get("https://maaji.buk.co/apidocs", headers={"auth_token": "EMVvA6ppoVTtRdoXgqu8JSWj"})
print("Status:", r.status_code)
html = r.text
print("HTML length:", len(html))

# Search for json/yaml specs or endpoint urls
matches = re.findall(r'(https?://[^\s"\'<>]+|/[^\s"\'<>]+\.(?:json|yaml|yml))', html)
print("URL / Spec matches:", set(matches))

# Look for swagger spec or swagger-ui config
swagger_specs = re.findall(r'url:\s*["\']([^"\']+)["\']', html)
print("Swagger URL configs:", swagger_specs)

# Save apidocs html to file to inspect
with open("apidocs.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Saved apidocs.html")
