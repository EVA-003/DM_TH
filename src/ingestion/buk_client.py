# -*- coding: utf-8 -*-
"""
Cliente HTTP para interactuar con la API REST de Buk Colombia.
"""
import time
import logging
import requests
from typing import Dict, Any, List, Optional
from config.settings import BUK_API_TOKEN, BUK_BASE_URL, REQUEST_TIMEOUT, MAX_RETRIES, PAGE_SIZE

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("BukClient")


class BukClient:
    def __init__(self, base_url: str = BUK_BASE_URL, token: str = BUK_API_TOKEN):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            "auth_token": self.token,
            "Accept": "application/json",
            "User-Agent": "Datamart-Nomina-Engine/1.0"
        })

    def _request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        clean_ep = endpoint.strip("/")
        url = f"{self.base_url}/{clean_ep}"
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self.session.request(method, url, params=params, timeout=REQUEST_TIMEOUT)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    wait_time = attempt * 2
                    logger.warning(f"Rate limit alcanzado (429). Esperando {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Error {response.status_code} al llamar a {url}: {response.text[:200]}")
                    return None
            except requests.exceptions.RequestException as e:
                logger.warning(f"Error de red (intento {attempt}/{MAX_RETRIES}) en {url}: {e}")
                time.sleep(attempt * 1.5)
        return None

    def get_paginated(self, endpoint: str, key_name: str = "data", extra_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        results = []
        page = 1
        params = {"page_size": PAGE_SIZE, "page": page}
        if extra_params:
            params.update(extra_params)

        logger.info(f"Iniciando extracción paginada para: /{endpoint}")
        while True:
            params["page"] = page
            data = self._request("GET", endpoint, params=params)
            if not data:
                break
            
            items = data.get(key_name, [])
            if not items:
                break
            
            results.extend(items)
            pagination = data.get("pagination", {})
            total_pages = pagination.get("total_pages", page)
            logger.info(f"  Página {page}/{total_pages} - {len(items)} registros obtenidos (Total acumulado: {len(results)})")

            if not pagination.get("next") or page >= total_pages:
                break
            
            page += 1
            time.sleep(0.1)  # Pausa preventiva para no saturar rate limit
            
        logger.info(f"Extracción finalizada para /{endpoint}: Total {len(results)} registros.")
        return results

    def get_employees(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {"status": status} if status else None
        return self.get_paginated("employees", extra_params=params)

    def get_active_employees(self, cutoff_date: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {"date": cutoff_date} if cutoff_date else None
        return self.get_paginated("employees/active", extra_params=params)

    def get_process_periods(self) -> List[Dict[str, Any]]:
        return self.get_paginated("process_periods")

    def get_items(self) -> List[Dict[str, Any]]:
        return self.get_paginated("items")

    def get_companies(self) -> List[Dict[str, Any]]:
        data = self._request("GET", "companies")
        return data.get("data", []) if data else []

    def get_areas(self) -> List[Dict[str, Any]]:
        return self.get_paginated("areas")

    def get_roles(self) -> List[Dict[str, Any]]:
        return self.get_paginated("roles")

    def get_locations(self) -> List[Dict[str, Any]]:
        return self.get_paginated("locations")

    def get_vacations(self) -> List[Dict[str, Any]]:
        return self.get_paginated("vacations")

    def get_absences(self) -> List[Dict[str, Any]]:
        return self.get_paginated("absences")

    def get_holidays(self) -> List[Dict[str, Any]]:
        return self.get_paginated("holidays")
