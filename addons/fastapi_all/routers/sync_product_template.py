from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Any
from odoo.api import Environment
from ...fastapi.dependencies import odoo_env
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
import os

router = APIRouter()
load_dotenv()
ODOO_SECRET = os.getenv('TOKEN')
auth_scheme = HTTPBearer()


# Model trả về cho các API
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None


# Model đầu vào cho sản phẩm
class ProductInput(BaseModel):
    product_id_ee: int = Field(..., description="ID sản phẩm ở hệ thống EE (kiểu số nguyên)")
    name: str = Field(..., description="Tên sản phẩm")
    list_price: float = Field(..., description="Giá bán sản phẩm")
    categ_id_ee: Optional[int] = Field(None, description="ID danh mục sản phẩm ở EE (kiểu số nguyên, có thể null)")
    default_code_ee: Optional[str] = Field(None, description="Mã nội bộ sản phẩm ở ee")


def get_category_id(env: Environment, categ_id_ee: int) -> Optional[int]:
    """
    Tìm kiếm danh mục sản phẩm trong model 'product.category' dựa trên external id (categ_id_ee).
    Nếu tìm thấy trả về internal id, nếu không trả về None.
    """
    cat = env["product.category"].sudo().search([("categ_id_ee", "=", categ_id_ee)], limit=1)
    return cat.id if cat else 1


@router.post("/product", response_model=APIResponse, tags=["Product"])
async def create_product(
        product: ProductInput,
        env: Environment = Depends(odoo_env),
        credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    token = credentials.credentials
    if token != ODOO_SECRET:
        raise HTTPException(
            status_code=403,
            detail=APIResponse(success=False, message="Mã bảo mật không đúng").model_dump()
        )

    # Kiểm tra xem sản phẩm đã tồn tại hay chưa dựa trên product_id_ee
    existing = env["product.template"].sudo().search([("product_id_ee", "=", product.product_id_ee)], limit=1)
    if existing:
        return APIResponse(
            success=True,
            message="Sản phẩm đã tồn tại",
            data={"product_id": existing.id}
        )

    # Nếu có thông tin danh mục, tìm kiếm internal id
    categ_id = 1
    if product.categ_id_ee is not None:
        categ_id = get_category_id(env, product.categ_id_ee)

    product_data = {
        "product_id_ee": product.product_id_ee,
        "name": product.name,
        "list_price": product.list_price,
        "categ_id": categ_id,
        "default_code": product.default_code_ee,
    }

    new_product = env["product.template"].sudo().create(product_data)
    return APIResponse(
        success=True,
        message="Sản phẩm được tạo thành công",
        data={"product_id": new_product.id}
    )


@router.put("/product/{product_id_ee}", response_model=APIResponse, tags=["Product"])
async def update_product(
        product_id_ee: int,
        product: ProductInput,
        env: Environment = Depends(odoo_env),
        credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    token = credentials.credentials
    if token != ODOO_SECRET:
        raise HTTPException(
            status_code=403,
            detail=APIResponse(success=False, message="Mã bảo mật không đúng").model_dump()
        )

    # Tìm kiếm sản phẩm theo product_id_ee
    product_record = env["product.template"].sudo().search([("product_id_ee", "=", product_id_ee)], limit=1)
    if not product_record:
        raise HTTPException(
            status_code=404,
            detail=APIResponse(success=False, message="Sản phẩm không tồn tại").model_dump()
        )

    # Nếu có thông tin danh mục, tìm internal id tương ứng
    categ_id = None
    if product.categ_id_ee is not None:
        categ_id = get_category_id(env, product.categ_id_ee)

    update_data = {
        "name": product.name,
        "list_price": product.list_price,
        "categ_id": categ_id,
        "default_code": product.default_code_ee,
    }

    product_record.sudo().write(update_data)
    return APIResponse(
        success=True,
        message="Sản phẩm được cập nhật thành công"
    )


@router.delete("/product/{product_id_ee}", response_model=APIResponse, tags=["Product"])
async def delete_product(
        product_id_ee: int,
        env: Environment = Depends(odoo_env),
        credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    token = credentials.credentials
    if token != ODOO_SECRET:
        raise HTTPException(
            status_code=403,
            detail=APIResponse(success=False, message="Mã bảo mật không đúng").model_dump()
        )

    # Tìm kiếm sản phẩm theo product_id_ee
    product_record = env["product.template"].sudo().search([("product_id_ee", "=", product_id_ee)], limit=1)
    if not product_record:
        raise HTTPException(
            status_code=404,
            detail=APIResponse(success=False, message="Sản phẩm không tồn tại").model_dump()
        )

    product_record.sudo().write({"active": False})
    return APIResponse(
        success=True,
        message="Sản phẩm đã được xóa thành công"
    )
