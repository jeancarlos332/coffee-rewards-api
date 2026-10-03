from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    phone: str = Field(min_length=7, max_length=30)
    pin: str = Field(min_length=4, max_length=6)


class LoginRequest(BaseModel):
    phone: str = Field(min_length=7, max_length=30)
    pin: str = Field(min_length=4, max_length=6)