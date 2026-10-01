from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models import Role
from datetime import datetime

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


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: Role

    model_config = ConfigDict(from_attributes=True)