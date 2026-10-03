from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_customer
from app.db.database import get_db
from app.db.models import Customer, Redemption

router = APIRouter(
    prefix="/api/admin/redemptions",
    tags=["Admin Redemptions"],
)


@router.get("/{code}")
def validate_redemption(
    code: str,
    db: Session = Depends(get_db),
):
    redemption = (
        db.query(Redemption)
        .filter(Redemption.code == code)
        .first()
    )

    if redemption is None:
        raise HTTPException(
            status_code=404,
            detail="Redemption not found",
        )

    if redemption.status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail="Redemption already used",
        )

    customer = (
        db.query(Customer)
        .filter(Customer.id == redemption.customer_id)
        .first()
    )

    return {
        "success": True,
        "valid": True,
        "redemption": {
            "id": redemption.id,
            "code": redemption.code,
            "status": redemption.status,
            "starsUsed": redemption.stars_used,
            "customer": {
                "name": customer.name,
                "phone": customer.phone,
            },
        },
    }
    
@router.post("/{code}/use")
def use_redemption(
    code: str,
    db: Session = Depends(get_db),
):
    redemption = (
        db.query(Redemption)
        .filter(Redemption.code == code)
        .with_for_update()
        .first()
    )

    if redemption is None:
        raise HTTPException(
            status_code=404,
            detail="Redemption not found",
        )

    if redemption.status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail="Redemption already used",
        )

    customer = (
        db.query(Customer)
        .filter(Customer.id == redemption.customer_id)
        .with_for_update()
        .first()
    )

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

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

    if total_stars < redemption.stars_used:
        raise HTTPException(
            status_code=400,
            detail="Customer does not have enough stars",
        )

    transaction = StarTransaction(
        customer_id=customer.id,
        amount=-redemption.stars_used,
        transaction_type="REDEEM",
        description="Bebida gratis",
    )

    db.add(transaction)

    redemption.status = "USED"
    redemption.used_at = func.now()

    db.commit()

    remaining_stars = total_stars - redemption.stars_used

    return {
        "success": True,
        "redemptionId": redemption.id,
        "status": redemption.status,
        "starsUsed": redemption.stars_used,
        "remainingStars": remaining_stars,
    }