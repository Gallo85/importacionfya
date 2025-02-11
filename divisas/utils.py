import requests
from django.conf import settings

def obtener_dolar(tipo="blue"):
    """
    Obtiene la cotización del dólar según el tipo (blue, oficial, etc.)
    """
    endpoint = settings.DOLAR_API_ENDPOINT
    if not endpoint:
        print("⚠️ ERROR: La variable DOLAR_API_ENDPOINT no está configurada en settings.py")
        return None

    try:
        response = requests.get(endpoint, timeout=5)  # Limita el tiempo de espera a 5 segundos
        response.raise_for_status()  # Lanza un error si la API no responde correctamente
        datos = response.json()

        if tipo in datos:
            return datos[tipo].get("venta", None)
        else:
            print(f"⚠️ ERROR: No se encontró el tipo de cambio '{tipo}' en la API")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR en la solicitud a la API: {e}")
        return None
