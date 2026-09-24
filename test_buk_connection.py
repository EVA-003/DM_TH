# -*- coding: utf-8 -*-
import os, sys, json, requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def get_config():
    token = os.getenv('BUK_API_TOKEN')
    tenant = os.getenv('BUK_TENANT')
    base_url = os.getenv('BUK_BASE_URL')

    if not token:
        print('[ERROR] La variable de entorno BUK_API_TOKEN no esta configurada.')
        print('Por favor configura BUK_API_TOKEN antes de ejecutar este script.')
        print('Ejemplo PowerShell:')
        print('  $env:BUK_API_TOKEN = "tu_api_key"')
        print('  $env:BUK_TENANT = "tu_subdominio"')
        sys.exit(1)

    if not tenant and not base_url:
        print('[ERROR] Debes configurar BUK_TENANT (o BUK_BASE_URL).')
        print( 'Ejemplo PowerShell: $env:BUK_TENANT = "maaji"' )
        sys.exit(1)

    if not base_url:
        base_url = f'https://{tenant}.buk.co/api/v1/colombia'

    return {
        'token': token,
        'tenant': tenant or 'custom',
        'base_url': base_url.rstrip('/')
    }

def test_connection():
    config = get_config()
    headers = {
        'auth_token': config['token'],
        'Accept': 'application/json',
        'User-Agent': 'Datamart-Nomina-Validator/1.0'
    }

    url = config['base_url'] + '/employees'
    params = {
        'page_size': 5,
        'page': 1
    }

    masked_token = ('*' * 8) + (config['token'][-4:] if len(config['token']) >= 4 else '***')
    print('=' * 60)
    print('PRUEBA DE CONEXION BUK COLOMBIA API')
    print('=' * 60)
    print('Target URL Base: ' + config['base_url'])
    print('Endpoint Test : ' + url)
    print('Token cargado : ' + masked_token)
    print('Enviando solicitud GET...')

    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        print('Status Code   : ' + str(response.status_code))

        if response.status_code == 200:
            data = response.json()
            print('[EXITO] Autenticacion y consulta exitosas!')
            print('-' * 60)
            
            if isinstance(data, dict):
                print('Llaves de respuesta: ' + str(list(data.keys())))
                employees = data.get('data', data.get('employees', []))
                pagination = data.get('pagination', {})
                if pagination:
                    print('Paginacion reportada: ' + str(pagination))
            elif isinstance(data, list):
                employees = data
            else:
                employees = []

            print('Registros en muestra recibida: ' + str(len(employees)))

            if employees and isinstance(employees[0], dict):
                sample_employee = employees[0]
                print('-' * 60)
                print('CAMPOS DEVUELTOS EN OBJETO EMPLEADO:')
                for key in sorted(sample_employee.keys()):
                    val_type = type(sample_employee[key]).__name__
                    print('  - ' + key + ' (' + val_type + ')')
                print('-' * 60)
                print('Muestra de campos laborales principales (sin datos sensibles):')
                safe_fields = ['id', 'document_type', 'status', 'start_date', 'end_date', 'area', 'role', 'company']
                for sf in safe_fields:
                    if sf in sample_employee:
                        print('    ' + sf + ': ' + str(sample_employee[sf]))
            
            print('=' * 60)
            print('Conexion validada exitosamente. Listo para siguientes fases.')
            return True

        elif response.status_code == 401:
            print('[ERROR 401 - Unauthorized] Token invalido o no autorizado.')
            print('Verifica que el API Key sea correcto y este activo.')
        elif response.status_code == 403:
            print('[ERROR 403 - Forbidden] Permisos insuficientes o bloqueo por Whitelist de IP.')
            print('1. Verifica que el token tenga permiso de lectura en Empleados.')
            print('2. Revisa en Buk si la empresa tiene habilitada Whitelist de IPs.')
        elif response.status_code == 404:
            print('[ERROR 404 - Not Found] Endpoint no encontrado.')
            print('Verifica si el subdominio o la ruta del pais es correcta: ' + url)
            print('Nota: Algunas instancias usan .buk.cl en vez de .buk.co.')
        else:
            print('[ERROR ' + str(response.status_code) + '] Respuesta: ' + response.text[:300])
        
        return False

    except requests.exceptions.RequestException as e:
        print('[ERROR DE RED] No se pudo establecer conexion con el servidor: ' + str(e))
        return False

if __name__ == '__main__':
    test_connection()
