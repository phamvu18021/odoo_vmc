from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Annotated
from ..schemas.order import APIResponse
from odoo.api import Environment
from ...fastapi.dependencies import odoo_env
from dotenv import load_dotenv
import os
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import date

router = APIRouter()

load_dotenv()
ODOO_SECRET = os.getenv('TOKEN')

auth_scheme = HTTPBearer()


class LoyaltyRule(BaseModel):
    product_category_id: Optional[int] = Field(None, description="ID danh mục sản phẩm áp dụng")
    product_ids: Optional[List[int]] = Field(None, description="Danh sách ID sản phẩm áp dụng")
    minimum_qty: int = Field(..., description="Số lượng tối thiểu")
    minimum_amount: float = Field(..., description="Giá trị đơn hàng tối thiểu")
    product_domain: str = Field(..., description="Điều kiện lọc sản phẩm (domain)")
    reward_point_mode: Literal["order", "money", "unit"] = Field(
        ..., description="Phương thức tính điểm: 'order', 'money' hoặc 'unit'"
    )
    code: Optional[str] = Field(None, description="Mã giảm giá (nếu có)")
    reward_point_split: int = Field(..., description="Số lần chia nhỏ điểm thưởng")
    reward_point_amount: int = Field(..., description="Số điểm thưởng (grant points)")


class LoyaltyReward(BaseModel):
    reward_type: Literal["discount", "product"] = Field(
        ..., description="Loại phần thưởng: 'discount' hoặc 'product'"
    )
    discount_mode: Optional[Literal["percent", "per_point", "per_order"]] = Field(
        "percent", description="Cách giảm giá (nếu áp dụng discount)"
    )
    discount: Optional[float] = Field(None, description="Giá trị giảm giá")
    discount_max_amount: Optional[float] = Field(None, description="Giá trị giảm tối đa (nếu có)")
    discount_applicability: Optional[Literal["order", "specific", "cheapest"]] = Field(
        None, description="Phạm vi giảm giá"
    )
    discount_product_domain: Optional[str] = Field(None, description="Domain áp dụng giảm giá")
    reward_product_id: Optional[int] = Field(None, description="ID sản phẩm quà tặng (nếu reward_type là product)")
    reward_product_qty: Optional[int] = Field(None, description="Số lượng quà tặng")
    required_points: Optional[int] = Field(1, description="Số điểm cần để đổi (phải > 0)")
    description: Optional[str] = Field(..., description="Mô tả phần thưởng")


class LoyaltyProgramInput(BaseModel):
    id_ee: int = Field(..., description="ID chương trình ở hệ thống EE (custom field)")
    name: str = Field(..., description="Tên chương trình khuyến mãi")
    program_type: Literal["promotion", "promo_code", "buy_x_get_y"] = Field(
        ..., description="Loại chương trình"
    )
    date_to: Optional[date] = Field(None, description="Ngày hết hạn của chương trình (YYYY-MM-DD)")
    portal_point_name: str = Field(..., description="Tên hiển thị điểm trên portal")
    max_usage: Optional[int] = Field(None, description="Giới hạn số lần sử dụng")
    available_on: Optional[List[str]] = Field(
        None, description="Các ứng dụng áp dụng (ví dụ: sale, pos, website)"
    )
    trigger: Literal["auto", "with_code"] = Field(..., description="Kích hoạt chương trình")
    rule_ids: List[LoyaltyRule] = Field(..., description="Danh sách các quy tắc (rules)")
    reward_ids: List[LoyaltyReward] = Field(..., description="Danh sách các phần thưởng (rewards)")


def get_ecm_category_id(env, external_id: int) -> int:
    category = env["product.category"].sudo().search([("categ_id_ee", "=", external_id)], limit=1)
    if not category:
        raise HTTPException(
            status_code=404,
            detail=APIResponse(success=False,
                               message="Category with categ_id_ee {external_id} not found.").model_dump()
        )
    return category.id


def get_ecm_product_ids(env, external_ids: List[int]) -> List[int]:
    if not external_ids:
        return []
    product_ids = []
    for ext_id in external_ids:
        product = env["product.template"].sudo().search([("product_id_ee", "=", ext_id)], limit=1)
        if not product:
            raise HTTPException(
                status_code=404,
                detail=APIResponse(success=False,
                                   message="Product with product_id_ee {ext_id} not found.").model_dump()
            )
        product_ids.append(product.id)
    return product_ids


def get_ecm_reward_product_id(env, external_id: int) -> int:
    product = env["product.template"].sudo().search([("product_id_ee", "=", external_id)], limit=1)
    if not product:
        raise HTTPException(
            status_code=404,
            detail=APIResponse(success=False, message="Reward Product with product_id_ee {external_id} not found.").model_dump()
        )
    return product.id


@router.post("/loyalty-program", response_model=APIResponse)
async def create_loyalty_program(
        program: LoyaltyProgramInput,
        env: Annotated[Environment, Depends(odoo_env)],
        credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    token = credentials.credentials
    if token != ODOO_SECRET:
        raise HTTPException(
            status_code=403,
            detail=APIResponse(success=False, message="Mã bảo mật không đúng").model_dump()
        )
    try:
        # Xây dựng dữ liệu cho các rule từ input rule_ids
        rules_data = []
        for rule in program.rule_ids:
            ecm_category_id = None
            if rule.product_category_id is not None:
                try:
                    ecm_category_id = get_ecm_category_id(env, rule.product_category_id)
                except ValueError as e:
                    raise HTTPException(status_code=400, detail=APIResponse(success=False, message=str(e)).model_dump())
            # Tìm internal IDs của các sản phẩm dựa trên external IDs (product_id_ee)

            try:
                ecm_product_ids = get_ecm_product_ids(env, rule.product_ids)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=APIResponse(success=False, message=str(e)).model_dump())

            rules_data.append({
                "product_category_id": ecm_category_id,
                "product_ids": [(6, 0, ecm_product_ids)],
                "minimum_qty": rule.minimum_qty,
                "minimum_amount": rule.minimum_amount,
                "product_domain": rule.product_domain,
                "reward_point_mode": rule.reward_point_mode,
                "code": rule.code,
                "reward_point_split": rule.reward_point_split,
                "reward_point_amount": rule.reward_point_amount,
            })

        # Xây dựng dữ liệu cho các reward từ input reward_ids
        rewards_data = []
        for reward in program.reward_ids:
            rp_internal = None
            if reward.reward_type == "product":
                if reward.reward_product_id is None:
                    raise HTTPException(
                        status_code=400,
                        detail=APIResponse(success=False, message="reward_product_id is required for product rewards.").model_dump()
                    )
                try:
                    rp_internal = get_ecm_reward_product_id(env, reward.reward_product_id)
                except ValueError as e:
                    raise HTTPException(status_code=400, detail=APIResponse(success=False, message=str(e)).model_dump())
            rewards_data.append({
                "reward_type": reward.reward_type,
                # "description": reward.description,
                "discount_mode": reward.discount_mode,
                "discount": reward.discount,
                "discount_max_amount": reward.discount_max_amount,
                "discount_applicability": reward.discount_applicability,
                "discount_product_domain": reward.discount_product_domain,
                "reward_product_id": rp_internal,
                "reward_product_qty": reward.reward_product_qty,
                "required_points": reward.required_points,
            })

        # Tạo bản ghi Loyalty Program;
        # Chúng ta dùng các lệnh (0, 0, {vals}) để tạo child records cho các One2many
        program_data = {
            "id_ee": program.id_ee,
            "name": program.name,
            "program_type": program.program_type,
            "currency_id": 24,  # Giá trị mặc định, bạn có thể thay đổi theo cấu hình của bạn
            "portal_point_name": program.portal_point_name,
            "limit_usage": False if (program.max_usage is None or program.max_usage == 0) else True,
            "max_usage": program.max_usage,
            "date_to": program.date_to,  # Bổ sung trường date_to.
            "available_on": program.available_on,
            "trigger": program.trigger,
            "rule_ids": [(0, 0, rule) for rule in rules_data],
            "reward_ids": [(0, 0, reward) for reward in rewards_data],
        }
        program_record = env["loyalty.program"].sudo().create(program_data)
        return APIResponse(success=True, message="Loyalty program created successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=APIResponse(success=False, message=str(e)).model_dump())


@router.put("/loyalty-program/{id_ee}", response_model=APIResponse)
async def update_loyalty_program(
        id_ee: int,
        program: LoyaltyProgramInput,
        env: Annotated[Environment, Depends(odoo_env)],
        credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    token = credentials.credentials
    if token != ODOO_SECRET:
        raise HTTPException(
            status_code=403,
            detail=APIResponse(success=False, message="Mã bảo mật không đúng").model_dump()
        )
    try:
        # Tìm kiếm bản ghi Loyalty Program theo external ID (id_ee)
        program_record = env["loyalty.program"].sudo().search([("id_ee", "=", id_ee)], limit=1)
        if not program_record:
            raise HTTPException(
                status_code=404,
                detail=APIResponse(success=False, message="Loyalty program with given id_ee not found.").model_dump()
            )
        # Xử lý rule_ids: chuyển đổi external IDs cho danh mục và sản phẩm.
        rules_data = []
        for rule in program.rule_ids:
            ecm_category_id = None
            if rule.product_category_id is not None:
                try:
                    ecm_category_id = get_ecm_category_id(env, rule.product_category_id)
                except ValueError as e:
                    raise HTTPException(status_code=400, detail=APIResponse(success=False, message=str(e)).model_dump())
            ecm_product_ids = get_ecm_product_ids(env, rule.product_ids)
            rules_data.append({
                "product_category_id": ecm_category_id,
                "product_ids": [(6, 0, ecm_product_ids)],
                "minimum_qty": rule.minimum_qty,
                "minimum_amount": rule.minimum_amount,
                "product_domain": rule.product_domain,
                "reward_point_mode": rule.reward_point_mode,
                "code": rule.code,
                "reward_point_split": rule.reward_point_split,
                "reward_point_amount": rule.reward_point_amount,
            })

        # Xử lý reward_ids: nếu reward_type là "product", chuyển đổi external reward_product_id
        rewards_data = []
        for reward in program.reward_ids:
            rp_internal = None
            if reward.reward_type == "product":
                if reward.reward_product_id is None:
                    raise HTTPException(
                        status_code=400,
                        detail=APIResponse(success=False, message="reward_product_id is required for product rewards.").model_dump()
                    )
                try:
                    rp_internal = get_ecm_reward_product_id(env, reward.reward_product_id)
                except ValueError as e:
                    raise HTTPException(status_code=400, detail=APIResponse(success=False, message=str(e)).model_dump())
            rewards_data.append({
                "reward_type": reward.reward_type,
                "description": reward.description,
                "discount_mode": reward.discount_mode,
                "discount": reward.discount,
                "discount_max_amount": reward.discount_max_amount,
                "discount_applicability": reward.discount_applicability,
                "discount_product_domain": reward.discount_product_domain,
                "reward_product_id": rp_internal,
                "reward_product_qty": reward.reward_product_qty,
                "required_points": reward.required_points,
            })

        # Xây dựng dữ liệu cập nhật cho Loyalty Program.
        # Với các trường one2many, để thay thế toàn bộ con, ta xóa sạch các dòng hiện có (5,0,0) rồi tạo mới.
        update_data = {
            "name": program.name,
            "program_type": program.program_type,
            "portal_point_name": program.portal_point_name,
            "limit_usage": False if (program.max_usage is None or program.max_usage == 0) else True,
            "max_usage": program.max_usage,
            "date_to": program.date_to,  # Bổ sung trường date_to.
            "available_on": program.available_on,
            "trigger": program.trigger,
            "rule_ids": [(5, 0, 0)] + [(0, 0, rule) for rule in rules_data],
            "reward_ids": [(5, 0, 0)] + [(0, 0, reward) for reward in rewards_data],
        }
        program_record.sudo().write(update_data)
        return APIResponse(success=True, message="Loyalty program updated successfully")

    except Exception as e:
        raise HTTPException(status_code=500, detail=APIResponse(success=False, message=str(e)).model_dump())


@router.delete("/loyalty-program/{id_ee}", response_model=APIResponse)
async def deactivate_loyalty_program(
        id_ee: int,
        env: Annotated[Environment, Depends(odoo_env)],
        credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    token = credentials.credentials
    if token != ODOO_SECRET:
        raise HTTPException(
            status_code=403,
            detail=APIResponse(success=False, message="Mã bảo mật không đúng").model_dump()
        )
    program = env["loyalty.program"].sudo().search([("id_ee", "=", id_ee)], limit=1)
    if not program:
        raise HTTPException(
            status_code=404,
            detail=APIResponse(success=False, message="Loyalty program not found").model_dump()
        )

    program.sudo().write({"active": False})

    return APIResponse(success=True, message="Loyalty program deactivated")
