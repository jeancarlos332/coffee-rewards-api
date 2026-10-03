from pydantic import BaseModel


class RedemptionResponse(BaseModel):
    id: int
    code: str
    status: str
    starsUsed: int