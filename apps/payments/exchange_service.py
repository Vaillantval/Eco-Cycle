import logging
import requests
from django.core.cache import cache

logger = logging.getLogger(__name__)

_CACHE_PREFIX  = 'ecocycle_fx_htg_'
_CACHE_TIMEOUT = 3600   # 1 heure
_API_BASE      = 'https://open.er-api.com/v6/latest'


def get_htg_rate(from_currency: str) -> float | None:
    """
    Retourne combien de HTG vaut 1 unité de from_currency.
    Ex : get_htg_rate('USD') → 132.5 (1 USD = 132.5 HTG)
    Résultat mis en cache 1 heure.
    """
    from_currency = from_currency.upper()
    if from_currency == 'HTG':
        return 1.0

    cache_key = _CACHE_PREFIX + from_currency
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        resp = requests.get(f'{_API_BASE}/{from_currency}', timeout=5)
        data = resp.json()
        if data.get('result') == 'success':
            rate = data.get('rates', {}).get('HTG')
            if rate:
                cache.set(cache_key, float(rate), _CACHE_TIMEOUT)
                return float(rate)
    except Exception as e:
        logger.warning(f'[ExchangeService] Taux indisponible pour {from_currency}: {e}')

    return None


def convert_to_htg(amount, from_currency: str) -> float | None:
    """Convertit amount (en from_currency) → HTG."""
    rate = get_htg_rate(from_currency)
    if rate is None:
        return None
    return round(float(amount) * rate, 2)


def convert_from_htg(amount_htg, to_currency: str) -> float | None:
    """Convertit amount_htg (en HTG) → to_currency."""
    to_currency = to_currency.upper()
    if to_currency == 'HTG':
        return round(float(amount_htg), 2)
    rate = get_htg_rate(to_currency)
    if rate is None or rate == 0:
        return None
    return round(float(amount_htg) / rate, 2)
