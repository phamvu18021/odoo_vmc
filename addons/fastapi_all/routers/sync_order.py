from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from odoo.api import Environment
from pydantic import BaseModel, Field
from typing import List, Optional
from ...fastapi.dependencies import odoo_env
from ..schemas.order import APIResponse
import os
import logging

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

_logger = logging.getLogger(__name__)

router = APIRouter()
load_dotenv()
ODOO_SECRET = os.getenv("TOKEN")
auth_scheme = HTTPBearer()


def get_auth_token(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    return credentials.credentials


class SyncOrderItem(BaseModel):
    product_id_ee: int
    quantity: int
    price: float


class SyncOrderRequest(BaseModel):
    order_id_ee: int
    partner_name: str
    partner_phone: Optional[str]
    partner_email: str
    promotion_id_ee: Optional[int]
    items: List[SyncOrderItem]
    total_price: float
    state: str  # draft, sale, done, cancel


@router.post("/sync_order", response_model=APIResponse)
def sync_order(
        data: SyncOrderRequest,
        env: Annotated[Environment, Depends(odoo_env)],
        token: str = Depends(get_auth_token),
):
    if token != ODOO_SECRET:
        raise HTTPException(status_code=403,
                            detail=APIResponse(success=False, message="Mã bảo mật không đúng").model_dump())

    try:
        Order = env["sale.order"].sudo()
        order = Order.search([("order_id_ee", "=", data.order_id_ee)], limit=1)

        if order:
            order.write({"state": data.state})
            return APIResponse(success=True, message="Cập nhật trạng thái đơn hàng thành công")

        Partner = env["res.partner"].sudo()
        partner = Partner.search([("email", "=", data.partner_email)], limit=1)
        if not partner:
            partner = Partner.create({
                "name": data.partner_name,
                "phone": data.partner_phone,
                "email": data.partner_email
            })

        order = Order.create({
            "partner_id": partner.id,
            "state": "draft",
            "order_id_ee": data.order_id_ee
        })

        Product = env["product.template"].sudo()
        for item in data.items:
            product = Product.search([("product_id_ee", "=", item.product_id_ee)], limit=1)
            if not product:
                raise HTTPException(status_code=400, detail=APIResponse(success=False,
                                                                        message=f"Không tìm thấy sản phẩm {item.product_id_ee}").model_dump())
            env["sale.order.line"].sudo().create({
                "order_id": order.id,
                "product_id": product.id,
                "product_uom_qty": item.quantity,
                "price_unit": item.price,
                "name": product.name
            })

        # Áp dụng chương trình khuyến mãi nếu có
        if data.promotion_id_ee:
            Program = env["loyalty.program"].sudo()
            program = Program.search([("id_ee", "=", data.promotion_id_ee)], limit=1)
            if not program:
                raise HTTPException(status_code=400, detail=APIResponse(success=False,
                                                                        message="Không tìm thấy chương trình khuyến mãi").model_dump())

            order._remove_promotion_lines()

            selected_reward = None
            selected_coupon = None
            claimable_rewards = order._get_claimable_rewards() or {}

            if program.program_type == "promo_code":
                _logger.info("check promo code")
                coupon_code = program.rule_ids[0].code if program.rule_ids else ""
                _logger.info(f"Applying coupon code: {coupon_code}")

                wizard = env["sale.loyalty.coupon.wizard"].sudo().create({
                    "order_id": order.id,
                    "coupon_code": coupon_code
                })
                wizard.action_apply()
                order._update_programs_and_rewards()
                update_claimable_rewards = order._get_claimable_rewards() or {}

                for coupon, rewards in update_claimable_rewards.items():
                    for reward in rewards:
                        if reward.program_id.id == program.id:
                            selected_reward = reward
                            selected_coupon = coupon
                            break
                    if selected_reward:
                        break

                if selected_reward:
                    _logger.info("have selected reward")
                    order._apply_program_reward(selected_reward, selected_coupon)
                else:
                    _logger.warning("Không tìm thấy phần thưởng phù hợp sau khi apply mã.")
            else:
                for coupon, rewards in claimable_rewards.items():
                    for reward in rewards:
                        if reward.program_id.id == program.id:
                            selected_reward = reward
                            selected_coupon = coupon
                            break
                    if selected_reward:
                        break
                if selected_reward:
                    order._apply_program_reward(selected_reward, selected_coupon)

        if abs(order.amount_total - data.total_price) > 1e-6:
            raise HTTPException(status_code=400, detail=APIResponse(success=False,
                                                                    message="Giá trị đơn hàng không khớp với hệ thống" + str(
                                                                        order.amount_total)).model_dump())

        order.write({"state": data.state})

        return APIResponse(success=True, message="Đồng bộ đơn hàng thành công")

    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=APIResponse(success=False, message=f"Lỗi hệ thống: {str(e)}").model_dump())
