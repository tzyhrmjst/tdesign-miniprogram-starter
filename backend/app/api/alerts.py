from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional

from app.services.alert_service import create_alert, delete_alert, list_alerts, list_histories, update_alert

router = APIRouter(tags=["alerts"])

DEMO_PREFIX = "demo_"


def _require_real_openid(openid):
    if not openid:
        raise HTTPException(status_code=400, detail="openid is required")
    if openid.startswith(DEMO_PREFIX):
        raise HTTPException(status_code=401, detail="wechat login is required")


def _check_ownership(openid, rule_id):
    from app.db.database import get_conn

    with get_conn() as conn:
        row = conn.execute("SELECT openid FROM alert_rules WHERE id = ?", (rule_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="alert rule not found")
    if row["openid"] != openid:
        raise HTTPException(status_code=403, detail="access denied")


class AlertPayload(BaseModel):
    openid: Optional[str] = None
    name: str
    direction: str
    target_price: float = Field(gt=0)
    unit: str
    cooldown_minutes: int = Field(default=720, gt=0)
    enabled: bool = True


class StatusPayload(BaseModel):
    openid: str
    enabled: bool


@router.get("/api/alerts")
def alerts(openid: str):
    return {"success": True, "data": list_alerts(openid)}


@router.post("/api/alerts")
def create(payload: AlertPayload):
    _require_real_openid(payload.openid)
    return {"success": True, "data": create_alert(payload.model_dump())}


@router.put("/api/alerts/{rule_id}")
def update(rule_id: int, payload: AlertPayload):
    _require_real_openid(payload.openid)
    _check_ownership(payload.openid, rule_id)
    return {"success": True, "data": update_alert(rule_id, payload.model_dump(exclude_none=True))}


@router.patch("/api/alerts/{rule_id}/status")
def status(rule_id: int, payload: StatusPayload):
    _require_real_openid(payload.openid)
    _check_ownership(payload.openid, rule_id)
    return {"success": True, "data": update_alert(rule_id, {"enabled": payload.enabled})}


@router.delete("/api/alerts/{rule_id}")
def delete(rule_id: int, openid: str = Query(...)):
    _require_real_openid(openid)
    _check_ownership(openid, rule_id)
    delete_alert(rule_id)
    return {"success": True}


@router.get("/api/alert-history")
def history(openid: str):
    return {"success": True, "data": list_histories(openid)}
