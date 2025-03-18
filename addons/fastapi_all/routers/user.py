import os
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from typing import Annotated
from odoo.api import Environment
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import pytz
from ..schemas.user import RegisterRequest, ActivateAccountRequest, LoginRequest, \
    UserInfoResponse, UpdateUserInfoRequest, ChangePasswordRequest, CheckEmailRequest, ReissuePasswordRequest, UserInfo
from ...fastapi.dependencies import odoo_env

router = APIRouter()

load_dotenv()
ODOO_SECRET = os.getenv('TOKEN')
JWT_SECRET = os.getenv('JWT_SECRET')
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRY_DAYS = 2

auth_scheme = HTTPBearer()


# def create_jwt_token(user_id: int):
#     expiration = datetime.now(pytz.utc) + timedelta(days=TOKEN_EXPIRY_DAYS)
#     payload = {"id": user_id, "exp": expiration}
#     return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_jwt_token(user_id: int):
    expiration = datetime.now(pytz.utc) + timedelta(days=TOKEN_EXPIRY_DAYS)
    payload = {
        "id": user_id,
        "exp": int(expiration.timestamp())  # Convert datetime to UNIX timestamp
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt_token(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail={"error": "Token đã hết hạn"})
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail={"error": "Token không hợp lệ"})


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
        if existing_partner and existing_partner.password and existing_partner.status:
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
        raise HTTPException(status_code=500, detail={"error": str(e)})


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
        token = create_jwt_token(partner.id)

        return {
            "success": "Đăng nhập thành công",
            "token": token,
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
        env: Annotated[Environment, Depends(odoo_env)],
        credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    token_data = decode_jwt_token(credentials.credentials)
    try:
        partner = env['res.partner'].sudo().browse(token_data["id"])
        if not partner.exists():
            return {"error": "Không tìm thấy tài khoản"}

        user_info = UserInfo(
            career=partner.function,
            name=partner.name,
            email=partner.email,
            phone=partner.phone,
            age=partner.age,
            gender=partner.gender,
        )

        return {"success": "Lấy thông tin thành công", "user_info": user_info}
    except Exception as e:
        return HTTPException(status_code=500, detail={"error": str(e)})


@router.post("/update_user_info")
async def update_user_info(
        request: UpdateUserInfoRequest,
        env: Annotated[Environment, Depends(odoo_env)],
        credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    token_data = decode_jwt_token(credentials.credentials)

    try:
        # Lấy đối tượng res.partner dựa trên partner_id
        partner = env['res.partner'].sudo().browse(token_data["id"])

        # Kiểm tra sự tồn tại của đối tượng
        if not partner.exists():
            return {"error": "Không tìm thấy tài khoản"}

        # Cập nhật thông tin đối tượng với các dữ liệu mới
        update_data = {
            'function': request.career,
            'name': request.name,
            'email': request.email,
            'age': request.age,
            'phone': request.phone,
            'gender': request.gender,
        }
        partner.sudo().write(update_data)

        return {"success": "Cập nhật thông tin thành công"}
    except Exception as e:
        return HTTPException(status_code=500, detail={"error": str(e)})


@router.post("/change_password")
async def change_password(
        request: ChangePasswordRequest,
        env: Annotated[Environment, Depends(odoo_env)],
        credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    token_data = decode_jwt_token(credentials.credentials)

    try:
        # Lấy đối tượng res.partner dựa trên session_log_id
        partner = env['res.partner'].sudo().browse(token_data["id"])

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
        return HTTPException(status_code=500, detail={"error": str(e)})


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
        if not partner.status and not partner.password:
            return {"exists": False, "message": "Email chưa được đăng ký"}
        if not partner.status and partner.password:
            return {"exists": False, "message": "Email chưa được kích hoạt"}
        return {"exists": True, "message": "Email đã tồn tại"}
    except Exception as e:
        return HTTPException(status_code=500, detail={"error": str(e)})


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
        return HTTPException(status_code=500, detail={"error": str(e)})
