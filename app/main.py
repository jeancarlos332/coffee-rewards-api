from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import Base, engine
from app.db import models
from app.routes.orders import router as orders_router
from app.routes.auth import router as auth_router
from app.routes.me import router as me_router
from app.routes.redemptions import router as redemptions_router
from app.routes.admin_redemptions import router as admin_redemptions_router

Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Coffee Rewards API",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(orders_router)
app.include_router(auth_router)
app.include_router(me_router)
app.include_router(redemptions_router)
app.include_router(admin_redemptions_router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "coffee-rewards-api",
    }