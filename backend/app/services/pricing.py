from app.core.config import get_settings


def choose_reference_price(msrp_aud: float | None, rrp_aud: float | None, price_aud: float) -> float:
    for candidate in (msrp_aud, rrp_aud, price_aud):
        if candidate is not None and candidate > 0:
            return float(candidate)
    return float(price_aud)


def calculate_lkr_price(base_aud: float, exchange_rate: float, handling_fee_percent: float | None = None) -> float:
    settings = get_settings()
    fee = settings.handling_fee_percent if handling_fee_percent is None else handling_fee_percent
    subtotal = base_aud * exchange_rate
    return round(subtotal * (1 + fee / 100), 2)
