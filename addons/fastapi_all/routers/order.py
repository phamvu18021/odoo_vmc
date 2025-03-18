import os
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Union
import requests

from .user import decode_jwt_token
from odoo.api import Environment
from ..schemas.order import OrderItem, CreateOrderResponse, CreateOrderRequest, ApplyPromotionRequest, \
    ApplyPromoCodeRequest, OrderData, OrderUpdateRequest, UpdateOrderStatusRequest, APIResponse, \
    PromotionItem, PaymentConfirmationData, OrderStatusData
from ...fastapi.dependencies import odoo_env
from dotenv import load_dotenv

router = APIRouter()

load_dotenv()
ODOO_SECRET = os.getenv('TOKEN')

auth_scheme = HTTPBearer()
ALLOWED_STATUS_TRANSITIONS = {
    "draft": ["sale"],
    "sale": ["done", "cancel"]
}


def get_auth_token(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    return credentials.credentials  # Chỉ lấy token thay vì object HTTPAuthorizationCredentials


@router.post("/create_order", response_model=APIResponse)
def create_order(
        data: CreateOrderRequest,
        env: Annotated[Environment, Depends(odoo_env)],
        token: Optional[str] = Depends(get_auth_token)  # Dùng hàm tự viết thay vì `auth_scheme`
):
    if not token or token != ODOO_SECRET:
        raise HTTPException(
            status_code=403,
            detail=APIResponse(success=False, message="Mã bảo mật không đúng").model_dump()
        )

    try:
        # 1️⃣ Tìm hoặc tạo khách hàng
        partner = env["res.partner"].sudo().search([("email", "=", data.partner_email)], limit=1)
        if not partner:
            partner = env["res.partner"].sudo().create({
                "name": data.partner_name,
                "phone": data.partner_phone,
                "email": data.partner_email,
            })

        # 🔹 Tạo đơn hàng trong Odoo
        order = env["sale.order"].sudo().create({
            "partner_id": partner.id,
            "amount_total": 0,
            "state": "draft",
        })

        # 🔹 Thêm sản phẩm vào đơn hàng
        for item in data.items:
            env["sale.order.line"].sudo().create({
                "order_id": order.id,
                "product_id": item.product_id,
                "product_uom_qty": item.quantity,
                "price_unit": item.price_unit,
                "name": env["product.template"].browse(item.product_id).name,
            })
            item.name = env["product.template"].browse(item.product_id).name

        return APIResponse(
            success=True,
            message="Thêm đơn hàng thành công",
            data=OrderData(
                order_id=order.id,
                partner_name=partner.name,
                partner_phone=partner.phone,
                partner_email=partner.email,
                items=data.items,
                total_price=order.amount_total,
            )
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=APIResponse(success=False, message=f"Lỗi hệ thống: {str(e)}").model_dump()
        )


@router.get("/order/{order_id}", response_model=APIResponse)
def get_order_details(
        order_id: int,
        env: Annotated[Environment, Depends(odoo_env)],
        token: Optional[str] = Depends(get_auth_token)  # Dùng hàm tự viết thay vì `auth_scheme`
):
    if not token or token != ODOO_SECRET:
        raise HTTPException(
            status_code=403,
            detail=APIResponse(success=False, message="Mã bảo mật không đúng").model_dump()
        )

    try:
        # 🔹 Lấy đơn hàng
        order = env["sale.order"].sudo().browse(order_id)
        print(type(order_id), order_id)
        if not order.exists():
            return APIResponse(success=False, message="Order not found")

        # 🔹 Lấy thông tin chương trình khuyến mãi (nếu có)
        reward_line = next((line for line in order.order_line if hasattr(line, "reward_id") and line.reward_id), None)
        reward = reward_line.reward_id if reward_line else None

        # 🔹 Chuẩn bị dữ liệu đơn hàng
        order_data = OrderData(
            order_id=order.id,
            order_name=order.name,
            partner_name=order.partner_id.name,
            partner_email=order.partner_id.email,
            partner_phone=order.partner_id.phone or order.partner_id.mobile,
            items=[
                OrderItem(
                    product_id=line.product_id.id,
                    quantity=line.product_uom_qty,
                    price_unit=line.price_unit,
                    name=line.name,
                    is_reward_line=any([line.is_reward_line, line.discount > 0, line.price_unit == 0])
                ) for line in order.order_line
            ],
            reward=PromotionItem(
                promotion_id=reward.program_id.id,
                name=reward.program_id.name,
                reward_id=reward.id,
                reward_description=reward.description,
                discount=reward.discount,
                reward_conditions=reward.conditions_description if reward.conditions_description else None,
                reward_product_name=reward.reward_product_id.name if reward.reward_product_id else None,
                reward_product_price=reward.reward_product_id.list_price
                if reward.reward_product_id else None,
                program_type=reward.program_id.program_type,
                coupon_code=reward.program_id.rule_ids[0].code if reward.program_id.rule_ids else None,
                reward_type=reward.reward_type,
            ) if reward else None,
            total_price=order.amount_total,
            create_time=order.create_date.strftime("%Y-%m-%d %H:%M:%S"),
            update_recent=order.write_date.strftime("%Y-%m-%d %H:%M:%S") if order.write_date else None,
            status=order.state
        )

        return APIResponse(
            success=True,
            message="Lấy thông tin đơn hàng thành công",
            data=order_data
        )

    except Exception as e:
        return APIResponse(success=False, message=f"Lỗi hệ thống: {str(e)}")


@router.get("/promotions/{order_id}", response_model=APIResponse)
def get_claimable_promotions(
        order_id: int,
        env: Annotated[Environment, Depends(odoo_env)],
        token: Optional[str] = Depends(get_auth_token)  # Dùng hàm tự viết thay vì `auth_scheme`
):
    if not token or token != ODOO_SECRET:
        raise HTTPException(
            status_code=403,
            detail=APIResponse(success=False, message="Mã bảo mật không đúng").model_dump()
        )

    try:
        # 🔹 Lấy đơn hàng
        order = env["sale.order"].sudo().browse(int(order_id))

        if not order.exists():
            return APIResponse(success=False, message="Order not found")

        # 🔹 Kích hoạt tính năng khuyến mãi
        order.sudo()._update_programs_and_rewards()
        claimable_rewards = order._get_claimable_rewards()

        if not claimable_rewards:
            return APIResponse(
                success=True,
                message="Không có khuyến mãi áp dụng",
                data=[]
            )

        # 🔹 Xử lý dữ liệu khuyến mãi
        promotions = []

        for coupon, rewards in claimable_rewards.items():
            for reward in rewards:
                promo_data = PromotionItem(
                    promotion_id=reward.program_id.id,
                    name=reward.program_id.name,
                    reward_id=reward.id,
                    reward_description=reward.description,
                    discount=reward.discount,
                    reward_conditions=reward.conditions_description,
                    reward_product_name=reward.reward_product_id.name if reward.reward_product_id else None,
                    reward_product_price=reward.reward_product_id.list_price if reward.reward_product_id else None,
                    program_type=reward.program_id.program_type,
                    coupon_code=reward.program_id.rule_ids[0].code if reward.program_id.rule_ids else None,
                    reward_type=reward.reward_type
                )

                promotions.append(promo_data)

        return APIResponse(
            success=True,
            message="Lấy danh sách khuyến mãi thành công",
            data=promotions
        )

    except Exception as e:
        return APIResponse(success=False, message=f"Lỗi hệ thống: {str(e)}")


@router.put("/apply_promotion", response_model=APIResponse)
def apply_promotion(
        data: ApplyPromotionRequest,
        env: Annotated[Environment, Depends(odoo_env)],
        token: Optional[str] = Depends(get_auth_token)  # Dùng hàm tự viết thay vì `auth_scheme`
):
    if not token or token != ODOO_SECRET:
        raise HTTPException(
            status_code=403,
            detail=APIResponse(success=False, message="Mã bảo mật không đúng").model_dump()
        )

    try:
        # 🔹 Lấy đơn hàng
        order = env["sale.order"].sudo().browse(int(data.order_id))

        if not order.exists():
            return APIResponse(success=False, message="Order not found")

        # 🔹 Xóa chương trình cũ trước khi áp dụng mới
        order._remove_promotion_lines()

        order.sudo()._update_programs_and_rewards()
        claimable_rewards = order._get_claimable_rewards()

        selected_reward = None
        selected_coupon = None

        for coupon, rewards in claimable_rewards.items():
            for reward in rewards:
                if reward.program_id.id == data.promotion_id:
                    selected_reward = reward
                    selected_coupon = coupon
                    break
            if selected_reward:
                break

        if not selected_reward:
            return APIResponse(success=False, message="Không tìm thấy phần thưởng phù hợp sau khi áp dụng.")

        # 🔹 Áp dụng chương trình khuyến mãi
        order._apply_program_reward(selected_reward, selected_coupon)

        # 🔹 Chuẩn bị dữ liệu đơn hàng sau khi áp dụng khuyến mãi
        order_data = OrderData(
            order_id=order.id,
            partner_name=order.partner_id.name,
            partner_email=order.partner_id.email,
            partner_phone=order.partner_id.phone or order.partner_id.mobile,
            items=[
                OrderItem(
                    product_id=line.product_id.id,
                    quantity=line.product_uom_qty,
                    price_unit=line.price_unit,
                    name=line.name,
                    is_reward_line=any([line.is_reward_line, line.discount > 0, line.price_unit == 0])
                ) for line in order.order_line
            ],
            reward=PromotionItem(
                promotion_id=selected_reward.program_id.id,
                name=selected_reward.program_id.name,
                reward_id=selected_reward.id,
                reward_description=selected_reward.description,
                discount=selected_reward.discount,
                reward_conditions=selected_reward.conditions_description if selected_reward.conditions_description else None,
                reward_product_name=selected_reward.reward_product_id.name if selected_reward.reward_product_id else None,
                reward_product_price=selected_reward.reward_product_id.list_price
                if selected_reward.reward_product_id else None,
                program_type=selected_reward.program_id.program_type,
                coupon_code=selected_reward.program_id.rule_ids[
                    0].code if selected_reward.program_id.rule_ids else None,
                reward_type=selected_reward.reward_type,
            ) if selected_reward else None,
            total_price=order.amount_total,
            create_time=order.create_date.strftime("%Y-%m-%d %H:%M:%S"),
            update_recent=order.write_date.strftime("%Y-%m-%d %H:%M:%S") if order.write_date else None,
            status=order.state
        )

        return APIResponse(
            success=True,
            message="Áp dụng chương trình khuyến mãi thành công",
            data=order_data
        )

    except Exception as e:
        return APIResponse(success=False, message=f"Lỗi hệ thống: {str(e)}")


@router.put("/apply_promo_code", response_model=APIResponse)
def apply_promo_code(
        data: ApplyPromoCodeRequest,
        env: Annotated[Environment, Depends(odoo_env)],
        token: Optional[str] = Depends(get_auth_token)  # Dùng hàm tự viết thay vì `auth_scheme`
):
    if not token or token != ODOO_SECRET:
        raise HTTPException(
            status_code=403,
            detail=APIResponse(success=False, message="Mã bảo mật không đúng").model_dump()
        )

    try:
        order = env["sale.order"].sudo().browse(int(data.order_id))

        if not order.exists():
            return APIResponse(success=False, message="Order not found")

        order.sudo()._update_programs_and_rewards()

        # 🔹 Kiểm tra mã khuyến mãi có trong danh sách phần thưởng không
        claimable_rewards = order._get_claimable_rewards() or {}

        reward_found = any(
            data.promo_code == reward.program_id.rule_ids[0].code
            for rewards in claimable_rewards.values()
            for reward in rewards
            if reward.program_id.rule_ids
        )

        if not reward_found:
            # Nếu không có, tiến hành áp mã khuyến mãi
            order._remove_promotion_lines()
            wizard = env["sale.loyalty.coupon.wizard"].sudo().create({
                "order_id": order.id,
                "coupon_code": data.promo_code
            })
            wizard.action_apply()

        # 🔹 Kiểm tra lại danh sách phần thưởng sau khi áp mã giảm giá
        updated_rewards = order._get_claimable_rewards() or {}

        selected_reward = None
        selected_coupon = None

        for coupon, rewards in updated_rewards.items():
            for reward in rewards:
                if reward.program_id.rule_ids and reward.program_id.rule_ids[0].code == data.promo_code:
                    selected_reward = reward
                    selected_coupon = coupon
                    break
            if selected_reward:
                break

        if not selected_reward:
            return APIResponse(success=False, message="Không tìm thấy phần thưởng phù hợp sau khi áp dụng.")

        order._apply_program_reward(selected_reward, selected_coupon)

        # 🔹 Chuẩn bị dữ liệu đơn hàng sau khi áp dụng mã giảm giá
        order_data = OrderData(
            order_id=order.id,
            partner_name=order.partner_id.name,
            partner_email=order.partner_id.email,
            partner_phone=order.partner_id.phone or order.partner_id.mobile,
            items=[
                OrderItem(
                    product_id=line.product_id.id,
                    quantity=line.product_uom_qty,
                    price_unit=line.price_unit,
                    name=line.name,
                    is_reward_line=getattr(line, "is_reward_line", False)  # Dùng getattr để tránh lỗi
                ) for line in order.order_line
            ],
            reward=PromotionItem(
                promotion_id=selected_reward.program_id.id,
                name=selected_reward.program_id.name,
                reward_id=selected_reward.id,
                reward_description=selected_reward.description,
                discount=selected_reward.discount,
                reward_conditions=selected_reward.conditions_description if selected_reward.conditions_description else None,
                reward_product_name=selected_reward.reward_product_id.name if selected_reward.reward_product_id else None,
                reward_product_price=selected_reward.reward_product_id.list_price
                if selected_reward.reward_product_id else None,
                program_type=selected_reward.program_id.program_type,
                coupon_code=selected_reward.program_id.rule_ids[
                    0].code if selected_reward.program_id.rule_ids else None,
                reward_type=selected_reward.reward_type,
            ) if selected_reward else None,
            total_price=order.amount_total,
            create_time=order.create_date.strftime("%Y-%m-%d %H:%M:%S"),
            update_recent=order.write_date.strftime("%Y-%m-%d %H:%M:%S") if order.write_date else None,
            status=order.state
        )

        return APIResponse(
            success=True,
            message="Áp dụng mã khuyến mãi thành công",
            data=order_data
        )

    except Exception as e:
        return APIResponse(success=False, message=f"Lỗi hệ thống: {str(e)}")


@router.put("/order", response_model=APIResponse)
def update_order(
        data: OrderUpdateRequest,
        env: Annotated[Environment, Depends(odoo_env)],
        token: Optional[str] = Depends(get_auth_token)  # Dùng hàm tự viết thay vì `auth_scheme`
):
    if not token or token != ODOO_SECRET:
        raise HTTPException(
            status_code=403,
            detail=APIResponse(success=False, message="Mã bảo mật không đúng").model_dump()
        )

    try:
        # 🔹 Tìm hoặc tạo khách hàng theo email
        partner = env["res.partner"].sudo().search([("email", "=", data.partner_email)], limit=1)

        if partner:
            # Cập nhật thông tin khách hàng nếu đã tồn tại
            partner.sudo().write({
                "name": data.partner_name,
                "phone": data.partner_phone,
            })
        else:
            # Tạo mới khách hàng
            partner = env["res.partner"].sudo().create({
                "name": data.partner_name,
                "email": data.partner_email,
                "phone": data.partner_phone,
                "customer_rank": 1  # Xác định là khách hàng
            })

        # 🔹 Tìm đơn hàng theo order_id_ee
        order = env["sale.order"].sudo().browse(int(data.order_id))

        # Gán khách hàng vào đơn hàng
        order.sudo().write({"partner_id": partner.id})
        if data.items is not None:
            # Xóa tất cả sản phẩm hiện tại trong đơn hàng
            order.order_line.sudo().unlink()

            # Thêm sản phẩm mới vào đơn hàng
            new_order_lines = [(0, 0, {
                "product_id": item.product_id,
                "product_uom_qty": item.quantity,
                "price_unit": item.price_unit
            }) for item in data.items]

            order.sudo().write({"order_line": new_order_lines})

        # Lấy lại thông tin đơn hàng sau khi cập nhật
        order = env["sale.order"].sudo().browse(order.id)

        order_data = OrderData(
            order_id=order.id,
            partner_name=order.partner_id.name,
            partner_email=order.partner_id.email,
            partner_phone=order.partner_id.phone or order.partner_id.mobile,
            items=[
                OrderItem(
                    product_id=line.product_id.id,
                    quantity=line.product_uom_qty,
                    price_unit=line.price_unit,
                    name=line.name,
                    is_reward_line=False
                ) for line in order.order_line
            ],
            total_price=order.amount_total,
            create_time=order.create_date.strftime("%Y-%m-%d %H:%M:%S"),
            update_recent=order.write_date.strftime("%Y-%m-%d %H:%M:%S") if order.write_date else None,
            status=order.state
        )

        return APIResponse(
            success=True,
            message="Cập nhật đơn hàng thành công",
            data=order_data
        )

    except Exception as e:
        return APIResponse(success=False, message=f"Lỗi hệ thống: {str(e)}")


@router.put("/payment-confirmation/{order_id}", response_model=APIResponse)
def confirm_payment(
        order_id: int,
        env: Annotated[Environment, Depends(odoo_env)],
        token: Optional[str] = Depends(get_auth_token)  # Dùng hàm tự viết thay vì `auth_scheme`
):
    if not token or token != ODOO_SECRET:
        raise HTTPException(
            status_code=403,
            detail=APIResponse(success=False, message="Mã bảo mật không đúng").model_dump()
        )

    try:
        # 🔹 Tìm đơn hàng theo order_id
        order = env["sale.order"].sudo().browse(int(order_id))

        if not order:
            return APIResponse(success=False, message="Order not found")

        # Nếu chưa xác nhận thanh toán, cập nhật thành `True`
        if not order.customer_payment_confirmed:
            order.sudo().write({"customer_payment_confirmed": True})

        payment_data = PaymentConfirmationData(
            order_id=order.id,
            customer_payment_confirmed=order.customer_payment_confirmed
        )

        return APIResponse(
            success=True,
            message="Xác nhận thanh toán thành công",
            data=payment_data
        )

    except Exception as e:
        return APIResponse(success=False, message=f"Lỗi hệ thống: {str(e)}")


def sync_order_data(order):
    # sync_url = "https://webhook.site/5d04b972-d6ae-4a53-a4e6-78866b5a532a"
    sync_url = "https://sam.aumpilot.com/c1/api/saleOrders"
    headers = {"Content-Type": "application/json",
               "api-key": "1"
               }

    sync_data = {
        "partner_info": {
            "name": order.partner_id.name if order.partner_id else "",
            "phone": order.partner_id.phone if order.partner_id else "",
            "email": order.partner_id.email if order.partner_id else "",
        },
        "name": order.name,
        "th_order_ecm_id": order.id,
        "th_utm_source": "vstep",
        "ecm_type": "vstep",
        "date_order": order.date_order.strftime("%Y-%m-%dT%H:%M:%S"),
        "amount_total": order.amount_total,
        "th_status": "draft",
        "state": order.state,
        "th_sale_order": "apm",
        "order_lines": [
            {
                "product_uom_qty": line.product_uom_qty,
                "discount": line.discount if line.discount else 0,
                "product_id": int(line.product_id.product_id_sam) if line.product_id.product_id_sam else 0,
                "price_unit": line.price_unit,
                "is_reward_line": any([line.is_reward_line, line.discount > 0, line.price_unit == 0]),
                **({"reward_id_sam": line.reward_id.reward_id_sam} if any(
                    [line.is_reward_line, line.discount > 0, line.price_unit == 0]) else {})
            }
            for line in order.order_line
        ],
    }

    try:
        response = requests.post(sync_url, json=sync_data, headers=headers, timeout=40)
        response.raise_for_status()
        print(f"Đồng bộ thành công đơn hàng {order.id}")
    except requests.exceptions.RequestException as e:
        print(f"[SYNC ERROR] Không thể đồng bộ đơn hàng {order.id}: {str(e)}")


@router.put("/update-order-status/{order_id}", response_model=APIResponse)
def update_order_status(
        order_id: int,
        data: UpdateOrderStatusRequest,
        background_tasks: BackgroundTasks,
        env: Annotated[Environment, Depends(odoo_env)],
        token: str = Depends(get_auth_token)  # Dùng hàm tự viết thay vì `auth_scheme`
):
    if token != ODOO_SECRET:
        raise HTTPException(
            status_code=403,
            detail=APIResponse(success=False, message="Mã bảo mật không đúng").model_dump()
        )

    try:
        # 🔹 Tìm đơn hàng theo order_id
        order = env["sale.order"].sudo().browse(int(order_id))

        if not order:
            return APIResponse(success=False, message="Order not found")
        if data.status not in ALLOWED_STATUS_TRANSITIONS.get(order.state, []):
            raise HTTPException(
                status_code=400,
                detail=APIResponse(success=False,
                                   message=f"Không thể chuyển trạng thái từ '{order.state}' sang '{data.status}'").model_dump()
            )
        # 🔹 Cập nhật trạng thái đơn hàng
        order.sudo().write({"state": data.status})
        if order.state == "sale" and data.status == "sale":
            background_tasks.add_task(sync_order_data, order)
        order_status_data = OrderStatusData(
            order_id=order.id,
            status=order.state
        )

        return APIResponse(
            success=True,
            message="Cập nhật trạng thái đơn hàng thành công",
            data=order_status_data
        )

    except Exception as e:
        return APIResponse(success=False, message=f"Lỗi hệ thống: {str(e)}")


@router.get("/orders_history", response_model=APIResponse)
async def get_user_orders(
        env: Annotated[Environment, Depends(odoo_env)],
        credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    token_data = decode_jwt_token(credentials.credentials)

    try:
        # Lấy partner từ token
        partner = env['res.partner'].sudo().browse(token_data["id"])
        if not partner.exists():
            return APIResponse(success=False, message="Không tìm thấy tài khoản")

        # Truy vấn các đơn hàng có trạng thái hợp lệ
        valid_states = ["sale", "done", "cancel"]
        orders = env["sale.order"].sudo().search([
            ("partner_id", "=", partner.id),
            ("state", "in", valid_states)
        ])

        # Chuẩn bị danh sách đơn hàng
        order_list = []
        for order in orders:
            # Lấy thông tin chương trình khuyến mãi (nếu có)
            reward_line = next((line for line in order.order_line if hasattr(line, "reward_id") and line.reward_id),
                               None)
            reward = reward_line.reward_id if reward_line else None

            order_data = OrderData(
                order_id=order.id,
                order_name=order.name,
                partner_name=order.partner_id.name,
                partner_email=order.partner_id.email,
                partner_phone=order.partner_id.phone or order.partner_id.mobile,
                items=[
                    OrderItem(
                        product_id=line.product_id.id,
                        quantity=line.product_uom_qty,
                        price_unit=line.price_unit,
                        name=line.name,
                        is_reward_line=any([line.is_reward_line, line.discount > 0, line.price_unit == 0])
                    ) for line in order.order_line
                ],
                reward=PromotionItem(
                    promotion_id=reward.program_id.id,
                    name=reward.program_id.name,
                    reward_id=reward.id,
                    reward_description=reward.description,
                    discount=reward.discount,
                    reward_conditions=reward.conditions_description if reward.conditions_description else None,
                    reward_product_name=reward.reward_product_id.name if reward.reward_product_id else None,
                    reward_product_price=reward.reward_product_id.list_price if reward.reward_product_id else None,
                    program_type=reward.program_id.program_type,
                    coupon_code=reward.program_id.rule_ids[0].code if reward.program_id.rule_ids else None,
                    reward_type=reward.reward_type,
                ) if reward else None,
                total_price=order.amount_total,
                create_time=order.create_date.strftime("%Y-%m-%d %H:%M:%S"),
                update_recent=order.write_date.strftime("%Y-%m-%d %H:%M:%S") if order.write_date else None,
                status=order.state
            )
            order_list.append(order_data)

        return APIResponse(
            success=True,
            message="Lấy danh sách đơn hàng thành công",
            data=order_list
        )

    except Exception as e:
        return APIResponse(success=False, message=f"Lỗi hệ thống: {str(e)}")
