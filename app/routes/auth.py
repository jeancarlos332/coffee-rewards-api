from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_pin, verify_pin
from app.db.database import get_db
from app.db.models import Customer
from app.schemas.auth import LoginRequest, RegisterRequest

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


def normalize_phone(phone: str) -> str:
    return "".join(character for character in phone if character.isdigit())


def create_access_token(customer_id: int) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_expire_minutes
    )

    payload = {
        "sub": str(customer_id),
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm="HS256",
    )


@router.post("/register")
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
):
    phone = normalize_phone(data.phone)

    if not phone:
        raise HTTPException(
            status_code=400,
            detail="Invalid phone number",
        )

    if not data.pin.isdigit():
        raise HTTPException(
            status_code=400,
            detail="PIN must contain only numbers",
        )

    existing_customer = (
        db.query(Customer)
        .filter(Customer.phone == phone)
        .first()
    )

    if existing_customer:
        if existing_customer.pin_hash:
            raise HTTPException(
                status_code=409,
                detail="A customer with this phone already exists",
            )

        existing_customer.name = data.name.strip()
        existing_customer.pin_hash = hash_pin(data.pin)

        db.commit()
        db.refresh(existing_customer)

        access_token = create_access_token(existing_customer.id)

        return {
            "success": True,
            "accessToken": access_token,
            "tokenType": "bearer",
            "customer": {
                "id": existing_customer.id,
                "name": existing_customer.name,
                "phone": existing_customer.phone,
            },
        }

    customer = Customer(
        name=data.name.strip(),
        phone=phone,
        pin_hash=hash_pin(data.pin),
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    access_token = create_access_token(customer.id)

    return {
        "success": True,
        "accessToken": access_token,
        "tokenType": "bearer",
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone,
        },
    }


@router.post("/login")
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    phone = normalize_phone(data.phone)

    customer = (
        db.query(Customer)
        .filter(Customer.phone == phone)
        .first()
    )

    if customer is None or not customer.pin_hash:
        raise HTTPException(
            status_code=401,
            detail="Invalid phone or PIN",
        )

    if not verify_pin(data.pin, customer.pin_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid phone or PIN",
        )

    access_token = create_access_token(customer.id)

    return {
        "success": True,
        "accessToken": access_token,
        "tokenType": "bearer",
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone,
        },
    }