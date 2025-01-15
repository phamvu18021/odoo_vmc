import os
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from typing import Optional, Annotated
from odoo.api import Environment
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..schemas.user import RegisterRequest, ActivateAccountRequest, LoginRequest, LoginResponse, UserInfoRequest, \
    UserInfoResponse, UpdateUserInfoRequest, ChangePasswordRequest, CheckEmailRequest, ReissuePasswordRequest, UserInfo
from ...fastapi.dependencies import odoo_env

router = APIRouter()

load_dotenv()
ODOO_SECRET = os.getenv('TOKEN')

auth_scheme = HTTPBearer()


@router.post("/register", response_model=dict)
async def register(
        request: RegisterRequest,
        env: Annotated[Environment, Depends(odoo_env)],
        credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    token = credentials.credentials
    if token != ODOO_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret code")

    try:
        # Kiểm tra nếu email đã tồn tại
        existing_partner = env['res.partner'].sudo().search([('email', '=', request.email)])
        if existing_partner:
            return {"error": "Email đã tồn tại"}

        new_partner = env['res.partner'].sudo().create({
            'name': request.name,
            'email': request.email,
            'password': request.password,
            'phone': 0,
            'status': False
        })

        return {"success": "Tạo tài khoản thành công", "partner_id": new_partner.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@router.post("/activate_account", response_model=dict)
async def activate_account(
        request: ActivateAccountRequest,
        env: Annotated[Environment, Depends(odoo_env)],
        credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    token = credentials.credentials
    if token != ODOO_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret code")

    try:
        # Tìm kiếm record trong res.partner với email và mật khẩu
        partner = env['res.partner'].sudo().search([
            ('email', '=', request.email),
            ('password', '=', request.password),
            ('status', '=', False)
        ], limit=1)

        if partner:
            partner.sudo().write({'status': True})
            return {"success": "Kích hoạt tài khoản thành công", "partner_id": partner.id}
        else:
            return {"error": "Email hoặc mật khẩu không chính xác, hoặc tài khoản đã được kích hoạt"}
    except Exception as e:
        return HTTPException(status_code=500, detail={"error": str(e)})


@router.post("/login", response_model=dict)
async def login(
        request: LoginRequest,
        env: Annotated[Environment, Depends(odoo_env)],
        credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    token = credentials.credentials
    if token != ODOO_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret code")

    try:
        # Tìm kiếm tài khoản với email và mật khẩu
        partner = env['res.partner'].sudo().search([
            ('email', '=', request.email),
            ('password', '=', request.password)
        ], limit=1)

        if not partner:
            return {"error": "Sai tài khoản hoặc mật khẩu"}

        if partner.status == False:
            return {"error": "Tài khoản của bạn chưa được kích hoạt. Vui lòng kiểm tra email để kích hoạt."}

        return {
            "success": "Đăng nhập thành công",
            "partner_id": partner.id,
            "user": UserInfo(
                email=partner.email,
                name=partner.name,
                phone=partner.phone,
                gender=partner.gender,
                age=partner.age
            )
        }
    except Exception as e:
        return HTTPException(status_code=500, detail={"error": str(e)})


@router.post("/get_user_info", response_model=UserInfoResponse)
async def get_user_info(
        request: UserInfoRequest,
        env: Annotated[Environment, Depends(odoo_env)],
        credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    token = credentials.credentials
    if token != ODOO_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret code")

    try:
        partner = env['res.partner'].sudo().browse(request.partner_id)

        if not partner.exists():
            return {"error": "Không tìm thấy tài khoản"}

        user_info = UserInfo(
            name=partner.name,
            email=partner.email,
            phone=partner.phone,
            age=partner.age,
            gender=partner.gender,
        )

        return {"success": "Lấy thông tin thành công", "user_info": user_info}
    except Exception as e:
        return HTTPException(status_code=500, content={"error": str(e)})


@router.post("/update_user_info")
async def update_user_info(
        request: UpdateUserInfoRequest,
        env: Annotated[Environment, Depends(odoo_env)],
        credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    token = credentials.credentials
    if token != ODOO_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret code")

    try:
        # Lấy đối tượng res.partner dựa trên partner_id
        partner = env['res.partner'].sudo().browse(request.partner_id)

        # Kiểm tra sự tồn tại của đối tượng
        if not partner.exists():
            return {"error": "Không tìm thấy tài khoản"}

        # Cập nhật thông tin đối tượng với các dữ liệu mới
        update_data = {
            'name': request.name,
            'email': request.email,
            'age': request.age,
            'phone': request.phone,
            'gender': request.gender,
        }
        partner.sudo().write(update_data)

        return {"success": "Cập nhật thông tin thành công"}
    except Exception as e:
        return HTTPException(status_code=500, content={"error": str(e)})


@router.post("/change_password")
async def change_password(
        request: ChangePasswordRequest,
        env: Annotated[Environment, Depends(odoo_env)],
        credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    token = credentials.credentials
    if token != ODOO_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret code")

    try:
        # Lấy đối tượng res.partner dựa trên session_log_id
        partner = env['res.partner'].sudo().browse(request.session_log_id)

        # Kiểm tra sự tồn tại của đối tượng
        if not partner.exists():
            return {"error": "Không tìm thấy tài khoản"}

        # Kiểm tra mật khẩu cũ
        if partner.password != request.old_password:
            return {"error": "Mật khẩu cũ không đúng"}

        # Cập nhật mật khẩu mới
        partner.sudo().write({'password': request.new_password})

        return {"success": "Đổi mật khẩu thành công"}
    except Exception as e:
        return HTTPException(status_code=500, content={"error": str(e)})


@router.post("/check_email")
async def check_email(
        request: CheckEmailRequest,
        env: Annotated[Environment, Depends(odoo_env)],
        credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    token = credentials.credentials
    if token != ODOO_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret code")

    try:
        # Tìm kiếm partner với email
        partner = env['res.partner'].sudo().search([('email', '=', request.email)], limit=1)

        if not partner:
            return {"exists": False, "message": "Email không tồn tại"}

        return {"exists": True, "message": "Email đã tồn tại"}
    except Exception as e:
        return HTTPException(status_code=500, content={"error": str(e)})


@router.post("/reissue_password")
async def reissue_password(
        request: ReissuePasswordRequest,
        env: Annotated[Environment, Depends(odoo_env)],
        credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    token = credentials.credentials
    if token != ODOO_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret code")

    try:
        # Tìm kiếm tài khoản với email
        partner = env['res.partner'].sudo().search([('email', '=', request.email)], limit=1)

        if not partner:
            return {"error": "Email không tồn tại"}

        # Đặt lại mật khẩu mới
        partner.sudo().write({'password': request.new_password})

        return {"success": "Mật khẩu đã được cập nhật thành công", "partner_id": partner.id}
    except Exception as e:
        return HTTPException(status_code=500, content={"error": str(e)})
