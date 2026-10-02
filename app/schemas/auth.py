from enum import Enum

from pydantic import BaseModel, EmailStr, field_validator


class AuthType(str, Enum):
    COOKIE = "cookie"
    JWT = "jwt"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    auth_type: AuthType

    @field_validator("password")
    @classmethod
    def password_no_html(cls, v: str) -> str:
        if "<" in v or ">" in v:
            raise ValueError("La contraseña no puede contener '<' ni '>'")
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos