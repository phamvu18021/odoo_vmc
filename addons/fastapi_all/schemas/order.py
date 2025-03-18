from pydantic import BaseModel, field_validator
from typing import Any
from pydantic import BaseModel
from typing import List, Optional, Literal, Union


class PromotionItem(BaseModel):
    promotion_id: int
    name: str
    reward_id: int
    reward_description: Optional[str] = None
    reward_conditions: Optional[str] = None
    discount: Optional[int] = None
    program_type: str
    coupon_code: Optional[str] = None
    reward_type: Optional[str] = None
    reward_product_name: Optional[str] = None
    reward_product_price: Optional[int] = None

    @field_validator("coupon_code",
                     mode="before")
    def convert_false_to_none(cls, value):
        return value if value is not False else None


class OrderItem(BaseModel):
    product_id: int
    quantity: int
    price_unit: float
    is_reward_line: Optional[bool] = False
    name: Optional[str] = None
    image: Optional[str] = None


# 🔹 Schema cho danh sách khuyến mãi


class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None


class CreateOrderRequest(BaseModel):
    partner_name: Optional[str] = "public"
    partner_phone: Optional[str] = "09999999999"
    partner_email: Optional[str] = "public@gmail.com"
    items: List[OrderItem]


# Schema response API
class CreateOrderResponse(BaseModel):
    order_id: Optional[int] = None
    partner_name: Optional[str] = None
    partner_email: Optional[str] = None
    partner_phone: Optional[str] = None
    items: Optional[List[OrderItem]] = None
    total_price: Optional[float] = None


class OrderData(BaseModel):
    order_id: int
    order_name: Optional[str] = None
    partner_name: str
    partner_email: str
    partner_phone: Optional[str] = None
    items: Optional[List[OrderItem]] = None
    reward: Optional[PromotionItem] = None
    total_price: float
    create_time: Optional[str] = None
    update_recent: Optional[str] = None
    status: Optional[str] = None


# Schema request API


class ApplyPromotionRequest(BaseModel):
    order_id: int
    promotion_id: int


class ApplyPromoCodeRequest(BaseModel):
    order_id: int
    promo_code: str


class OrderUpdateRequest(BaseModel):
    order_id: int
    partner_name: str
    partner_phone: Optional[str] = None
    partner_email: str  # Email bắt buộc
    items: Optional[List[OrderItem]] = None


class UpdateOrderStatusRequest(BaseModel):
    status: Literal["sale", "done", "cancel"]


class PaymentConfirmationData(BaseModel):
    order_id: int
    customer_payment_confirmed: bool


class OrderStatusData(BaseModel):
    order_id: int
    status: str
