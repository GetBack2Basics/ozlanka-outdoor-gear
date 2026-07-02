from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.api.routes.auth import get_db
from app.models import AppSetting

router = APIRouter(prefix="/public", tags=["public"])

DEFAULTS = {
    "banner_title": "OzLanka Outdoor Gear",
    "banner_description": "Request outdoor gear from Australia with manual approval, LKR pricing, and clear shipping and customs terms.",
    "logo_image_url": "",
    "promo_title_l": "Shipping updates",
    "promo_text_l": "8 weeks shipping target",
    "promo_title_c": "Important",
    "promo_text_c": "Customer pays customs in Colombo",
    "promo_title_r": "Fees",
    "promo_text_r": "Handling fee defaults to 25%",
}

KEYS = list(DEFAULTS.keys())


@router.get("/settings")
def public_settings(db=Depends(get_db)):
    rows = db.execute(select(AppSetting).where(AppSetting.key.in_(KEYS))).scalars().all()
    settings = {row.key: row.value for row in rows}
    return JSONResponse({key: settings.get(key, DEFAULTS[key]) for key in KEYS})
