from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models import Role


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: Role

    model_config = ConfigDict(from_attributes=True)