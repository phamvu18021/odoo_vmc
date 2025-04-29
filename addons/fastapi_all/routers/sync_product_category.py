from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Any
from odoo.api import Environment
from ...fastapi.dependencies import odoo_env
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
import os
from typing import Optional, Any, Union
router = APIRouter()
load_dotenv()
ODOO_SECRET = os.getenv('TOKEN')
auth_scheme = HTTPBearer()


# Model trả về cho các API
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None


# Model đầu vào cho danh mục sản phẩm
class ProductCategoryInput(BaseModel):
    categ_id_ee: int = Field(..., description="ID danh mục sản phẩm ở EE")
    categ_name_ee: str = Field(..., description="Tên danh mục sản phẩm ở EE")
    categ_parent_id_ee: Optional[Union[int, str, None]] = Field(None,
                                                                description="ID danh mục sản phẩm cha ở EE (nếu có)")


def get_parent_category(env: Environment, parent_ext_id: int) -> Optional[int]:
    """
    Tìm kiếm danh mục cha dựa trên external id (categ_parent_id_ee).
    Nếu tìm thấy trả về internal id, nếu không thì trả về None.
    """
    parent_cat = env["product.category"].sudo().search([("categ_id_ee", "=", parent_ext_id)], limit=1)
    return parent_cat.id if parent_cat else None


@router.post("/product-category", response_model=APIResponse, tags=["Product Category"])
async def create_product_category(
        category: ProductCategoryInput,
        env: Environment = Depends(odoo_env),
        credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    token = credentials.credentials
    if token != ODOO_SECRET:
        raise HTTPException(
            status_code=403,
            detail=APIResponse(success=False, message="Mã bảo mật không đúng").model_dump()
        )

    # Kiểm tra xem đã có danh mục với categ_id_ee trùng chưa
    existing = env["product.category"].sudo().search([("categ_id_ee", "=", category.categ_id_ee)], limit=1)
    if existing:
        return APIResponse(
            success=True,
            message="Danh mục sản phẩm đã tồn tại",
        )

    # Nếu có thông tin cha, tìm kiếm internal id của danh mục cha
    parent_id = None
    if category.categ_parent_id_ee:
        parent_id = get_parent_category(env, category.categ_parent_id_ee)

    category_data = {
        "categ_id_ee": category.categ_id_ee,
        "name": category.categ_name_ee,
        "parent_id": parent_id,
    }

    new_category = env["product.category"].sudo().create(category_data)
    return APIResponse(
        success=True,
        message="Danh mục sản phẩm được tạo thành công",
    )


@router.put("/product-category/{categ_id_ee}", response_model=APIResponse, tags=["Product Category"])
async def update_product_category(
        categ_id_ee: int,
        category: ProductCategoryInput,
        env: Environment = Depends(odoo_env),
        credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    token = credentials.credentials
    if token != ODOO_SECRET:
        raise HTTPException(
            status_code=403,
            detail=APIResponse(success=False, message="Mã bảo mật không đúng").model_dump()
        )

    # Tìm kiếm danh mục theo categ_id_ee
    cat_record = env["product.category"].sudo().search([("categ_id_ee", "=", categ_id_ee)], limit=1)
    if not cat_record:
        raise HTTPException(
            status_code=404,
            detail=APIResponse(success=False, message="Danh mục sản phẩm không tồn tại").model_dump()
        )

    parent_id = None
    if category.categ_parent_id_ee:
        parent_id = get_parent_category(env, category.categ_parent_id_ee)

    update_data = {
        "name": category.categ_name_ee,
        "parent_id": parent_id,
    }

    cat_record.sudo().write(update_data)
    return APIResponse(
        success=True,
        message="Danh mục sản phẩm được cập nhật thành công"
    )


@router.delete("/product-category/{categ_id_ee}", response_model=APIResponse, tags=["Product Category"])
async def delete_product_category(
        categ_id_ee: int,
        env: Environment = Depends(odoo_env),
        credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    token = credentials.credentials
    if token != ODOO_SECRET:
        raise HTTPException(
            status_code=403,
            detail=APIResponse(success=False, message="Mã bảo mật không đúng").model_dump()
        )

    # Tìm danh mục theo categ_id_ee
    cat_record = env["product.category"].sudo().search([("categ_id_ee", "=", categ_id_ee)], limit=1)
    if not cat_record:
        raise HTTPException(
            status_code=404,
            detail=APIResponse(success=False, message="Danh mục sản phẩm không tồn tại").model_dump()
        )

    # Thực hiện xóa bản ghi
    cat_record.sudo().unlink()
    return APIResponse(
        success=True,
        message="Danh mục sản phẩm đã được xóa thành công"
    )
