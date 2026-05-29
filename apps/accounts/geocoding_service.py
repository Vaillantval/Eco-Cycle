import logging
import math
import requests

logger = logging.getLogger(__name__)

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Retourne la distance en km entre deux coordonnées GPS (formule haversine)."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi  = math.radians(lat2 - lat1)
    dlam  = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'
HEADERS = {'User-Agent': 'EcoCycle-Haiti/1.0 (contact@ecocyclehaiti.com)'}


def geocode_address(address: str, city: str) -> tuple[float, float] | None:
    """
    Convertit une adresse en (latitude, longitude) via Nominatim (OSM).
    Retourne None si introuvable ou en cas d'erreur.
    """
    query = ', '.join(filter(None, [address.strip(), city.strip(), 'Haiti']))
    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={'q': query, 'format': 'json', 'limit': 1, 'countrycodes': 'ht'},
            headers=HEADERS,
            timeout=5,
        )
        resp.raise_for_status()
        results = resp.json()
        if results:
            return float(results[0]['lat']), float(results[0]['lon'])
        # Retry sans l'adresse précise — juste la ville
        if city.strip():
            resp2 = requests.get(
                NOMINATIM_URL,
                params={'q': f'{city.strip()}, Haiti', 'format': 'json', 'limit': 1, 'countrycodes': 'ht'},
                headers=HEADERS,
                timeout=5,
            )
            resp2.raise_for_status()
            results2 = resp2.json()
            if results2:
                return float(results2[0]['lat']), float(results2[0]['lon'])
    except Exception as e:
        logger.warning('Geocoding error for "%s, %s": %s', address, city, e)
    return None
