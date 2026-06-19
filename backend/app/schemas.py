from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models import ApprovalStatus, RequestStatus, UserRole


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    approval_status: ApprovalStatus

    class Config:
        from_attributes = True


class ProductRead(BaseModel):
    id: int
    name: str
    source_name: str
    source_url: str | None = None
    sku: str | None = None
    category: str | None = None
    description: str | None = None
    image_url: str | None = None
    price_aud: float
    msrp_aud: float | None
    rrp_aud: float | None
    price_lkr: float
    handling_fee_percent: float
    exchange_rate_aud_lkr: float
    active: bool
    source_lastmod_at: datetime | None = None

    class Config:
        from_attributes = True


class RequestListCreate(BaseModel):
    product_name: str
    quantity: int = 1
    notes: str | None = None


class RequestListRead(BaseModel):
    id: int
    product_name: str
    quantity: int
    notes: str | None
    status: RequestStatus

    class Config:
        from_attributes = True


class ApproveUserPayload(BaseModel):
    user_id: int


class HandlingFeePayload(BaseModel):
    handling_fee_percent: float


class ScrapeResult(BaseModel):
    run_id: int
    message: str
