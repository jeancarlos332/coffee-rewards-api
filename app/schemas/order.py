from decimal import Decimal

from pydantic import BaseModel, Field


class CustomerOrderData(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    phone: str = Field(min_length=7, max_length=30)
    email: str | None = None
    address: str | None = None


class OrderCreate(BaseModel):
    orderId: str = Field(min_length=1, max_length=150)
    customer: CustomerOrderData
    total: Decimal = Field(gt=0)