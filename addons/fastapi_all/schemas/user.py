# schemas.py
from pydantic import BaseModel
from typing import List, Optional, Dict
from pydantic import BaseModel, field_validator


class UserInfo(BaseModel):
    name: Optional[str]
    email: Optional[str]
    image: Optional[str] = None
    age: Optional[int] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    career: Optional[str] = None

    @field_validator("name", "email", "image", "age", "phone",
                     "gender", "career",
                     mode="before")
    def convert_false_to_none(cls, value):
        return value if value is not False else None


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


class LoginResponse(BaseModel):
    success: Optional[str] = None
    user: Optional[UserInfo] = None
    error: Optional[str] = None


class UserInfoResponse(BaseModel):
    success: str
    user_info: UserInfo


class UpdateUserInfoRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    age: Optional[int] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    career: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class CheckEmailRequest(BaseModel):
    email: str


class ReissuePasswordRequest(BaseModel):
    email: str
    new_password: str
