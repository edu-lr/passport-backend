from enum import Enum

from pydantic import BaseModel, EmailStr


class AuthType(str, Enum):
    COOKIE = "cookie"
    JWT = "jwt"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    auth_type: AuthType


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos