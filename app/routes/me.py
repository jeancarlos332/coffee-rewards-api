from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.auth import get_current_customer
from app.core.config import settings
from app.db.database import get_db
from app.db.models import Customer, StarTransaction

router = APIRouter(
    prefix="/api/me",
    tags=["Customer"],
)


@router.get("")
def get_me(
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
):
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

    return {
        "id": customer.id,
        "name": customer.name,
        "phone": customer.phone,
        "stars": total_stars,
        "freeDrinkStars": settings.free_drink_stars,
        "canRedeem": total_stars >= settings.free_drink_stars,
    }