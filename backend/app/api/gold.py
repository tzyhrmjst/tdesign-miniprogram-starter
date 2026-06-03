from fastapi import APIRouter

from app.services.price_service import get_history, get_kline, get_latest_price

router = APIRouter(prefix="/api/gold", tags=["gold"])


@router.get("/latest")
def latest():
    return {"success": True, "data": get_latest_price()}


@router.get("/history")
def history(range: str = "1d"):
    limit = 288 if range == "1d" else 1000
    return {"success": True, "data": get_history(limit)}


@router.get("/kline")
def kline(period: int = 15, limit: int = 96, price_type: str = "sale"):
    return {"success": True, "data": get_kline(period, limit, price_type)}
