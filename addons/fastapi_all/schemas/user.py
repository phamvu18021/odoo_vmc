# schemas.py
from pydantic import BaseModel
from typing import List, Optional, Dict


class UserInfo(BaseModel):
    name: Optional[str]
    email: Optional[str]
    image: Optional[str] = None
    age: Optional[int] = None
    phone: Optional[str] = None
    gender: Optional[str] = None


class RegisterRequest(BaseModel):
    email: str
    name: str
    password: str


class ActivateAccountRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserInfoRequest(BaseModel):
    partner_id: int


class LoginResponse(BaseModel):
    success: Optional[str] = None
    partner_id: Optional[int] = None
    user: Optional[UserInfo] = None
    error: Optional[str] = None


class UserInfoResponse(BaseModel):
    success: str
    user_info: UserInfo


class UpdateUserInfoRequest(BaseModel):
    partner_id: int
    name: Optional[str] = None
    email: Optional[str] = None
    age: Optional[int] = None
    phone: Optional[str] = None
    gender: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    session_log_id: int
    old_password: str
    new_password: str


class CheckEmailRequest(BaseModel):
    email: str


class ReissuePasswordRequest(BaseModel):
    email: str
    new_password: str
