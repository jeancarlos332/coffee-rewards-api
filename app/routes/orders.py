from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.db.models import Customer, Order, StarTransaction
from app.schemas.order import OrderCreate


router = APIRouter(
    prefix="/api/orders",
    tags=["Orders"],
)


def normalize_phone(phone: str) -> str:
    return "".join(character for character in phone if character.isdigit())


def get_customer_stars(db: Session, customer_id: int) -> int:
    total = (
        db.query(func.coalesce(func.sum(StarTransaction.amount), 0))
        .filter(StarTransaction.customer_id == customer_id)
        .scalar()
    )

    return int(total or 0)


@router.post("")
def create_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
    x_api_key: str | None = Header(default=None),
):
    if x_api_key != settings.ordenio_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )

    # ---------------------------------------------------------
    # 1. Verificar si Ordenio ya envió este pedido
    # ---------------------------------------------------------

    existing_order = (
        db.query(Order)
        .filter(Order.order_id == data.orderId)
        .first()
    )

    if existing_order:
        total_stars = get_customer_stars(
            db,
            existing_order.customer_id,
        )

        return {
            "success": True,
            "orderId": existing_order.order_id,
            "starsEarned": 0,
            "totalStars": total_stars,
            "alreadyProcessed": True,
        }

    # ---------------------------------------------------------
    # 2. Normalizar teléfono
    # ---------------------------------------------------------

    phone = normalize_phone(data.customer.phone)

    if not phone:
        raise HTTPException(
            status_code=400,
            detail="Invalid customer phone",
        )

    # ---------------------------------------------------------
    # 3. Buscar o crear cliente
    # ---------------------------------------------------------

    customer = (
        db.query(Customer)
        .filter(Customer.phone == phone)
        .first()
    )

    if customer is None:
        customer = Customer(
            name=data.customer.name,
            phone=phone,
            pin_hash=None,
            email=data.customer.email,
            address=data.customer.address,
        )

        db.add(customer)
        db.flush()

    else:
        # Actualizamos los datos que vienen de Ordenio.
        customer.name = data.customer.name
        customer.email = data.customer.email
        customer.address = data.customer.address

    # ---------------------------------------------------------
    # 4. Calcular estrellas
    # ---------------------------------------------------------

    stars_earned = int(
        data.total // Decimal(1000)
    ) * settings.stars_per_1000

    # ---------------------------------------------------------
    # 5. Registrar pedido
    # ---------------------------------------------------------

    order = Order(
        order_id=data.orderId,
        customer_id=customer.id,
        total=data.total,
        stars_earned=stars_earned,
    )

    db.add(order)
    db.flush()

    # ---------------------------------------------------------
    # 6. Registrar movimiento de estrellas
    # ---------------------------------------------------------

    if stars_earned > 0:
        transaction = StarTransaction(
            customer_id=customer.id,
            amount=stars_earned,
            transaction_type="EARN",
            description=f"Estrellas por pedido {data.orderId}",
            order_id=data.orderId,
        )

        db.add(transaction)

    # ---------------------------------------------------------
    # 7. Guardar todo
    # ---------------------------------------------------------

    db.commit()

    # ---------------------------------------------------------
    # 8. Obtener saldo actualizado
    # ---------------------------------------------------------

    total_stars = get_customer_stars(
        db,
        customer.id,
    )

    return {
        "success": True,
        "orderId": data.orderId,
        "starsEarned": stars_earned,
        "totalStars": total_stars,
        "alreadyProcessed": False,
    }