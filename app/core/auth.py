import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.db.models import Customer

security = HTTPBearer()


def get_current_customer(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Customer:
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=["HS256"],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )

    customer_id = payload.get("sub")

    if not customer_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )

    customer = (
        db.query(Customer)
        .filter(Customer.id == int(customer_id))
        .first()
    )

    if customer is None:
        raise HTTPException(
            status_code=401,
            detail="Customer not found",
        )

    return customer