from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
import html
from app.models import Role
from datetime import datetime


def _sanitize(value: str) -> str:
    """Escapa caracteres HTML peligrosos para prevenir XSS."""
    return html.escape(value.strip())


class UserAdminOut(BaseModel):
    id: int
    email: EmailStr
    role: Role
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
 
    @field_validator("password")
    @classmethod
    def password_no_html(cls, v: str) -> str:
        if "<" in v or ">" in v:
            raise ValueError("La contraseña no puede contener '<' ni '>'")
        return v



class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: Role

    model_config = ConfigDict(from_attributes=True)