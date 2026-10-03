import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_customer
from app.core.config import settings
from app.db.database import get_db
from app.db.models import Customer, Redemption

router = APIRouter(
    prefix="/api/redemptions",
    tags=["Redemptions"],
)


@router.post("")
def create_redemption(
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
):
    # Calculamos las estrellas actuales
    from sqlalchemy import func
    from app.db.models import StarTransaction

    total_stars = (
        db.query(
            func.coalesce(
                func.sum(StarTransaction.amount),
                0,
            )
        )
        .filter(
            StarTransaction.customer_id == customer.id
        )
        .scalar()
    )

    total_stars = int(total_stars or 0)

    if total_stars < settings.free_drink_stars:
        raise HTTPException(
            status_code=400,
            detail="Not enough stars",
        )

    # Evitar múltiples QR pendientes
    existing_redemption = (
        db.query(Redemption)
        .filter(
            Redemption.customer_id == customer.id,
            Redemption.status == "PENDING",
        )
        .first()
    )

    if existing_redemption:
        return {
            "success": True,
            "id": existing_redemption.id,
            "code": existing_redemption.code,
            "status": existing_redemption.status,
            "starsUsed": existing_redemption.stars_used,
        }

    code = secrets.token_urlsafe(24)

    redemption = Redemption(
        customer_id=customer.id,
        stars_used=settings.free_drink_stars,
        code=code,
        status="PENDING",
    )

    db.add(redemption)
    db.commit()
    db.refresh(redemption)

    return {
        "success": True,
        "id": redemption.id,
        "code": redemption.code,
        "status": redemption.status,
        "starsUsed": redemption.stars_used,
    }