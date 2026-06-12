import requests

from app.core.config import get_settings


def get_aud_to_lkr_rate() -> float:
    settings = get_settings()
    try:
        response = requests.get(settings.fx_api_url, timeout=10)
        response.raise_for_status()
        payload = response.json()
        rate = payload.get("rates", {}).get("LKR")
        if rate:
            return float(rate)
    except Exception:
        pass
    return float(settings.fx_fallback_aud_lkr)
