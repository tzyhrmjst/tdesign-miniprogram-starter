import json
import os
import urllib.parse
import urllib.request

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["auth"])


class WxLoginPayload(BaseModel):
    code: str


@router.post("/wx-login")
def wx_login(payload: WxLoginPayload):
    appid = os.getenv("WECHAT_APPID")
    secret = os.getenv("WECHAT_SECRET")
    if not appid or not secret:
        raise HTTPException(status_code=503, detail="wechat credentials are not configured")

    params = urllib.parse.urlencode(
        {
            "appid": appid,
            "secret": secret,
            "js_code": payload.code,
            "grant_type": "authorization_code",
        }
    )
    url = f"https://api.weixin.qq.com/sns/jscode2session?{params}"

    with urllib.request.urlopen(url, timeout=8) as response:
        data = json.loads(response.read().decode("utf-8"))

    if data.get("errcode"):
        raise HTTPException(status_code=400, detail=data)
    if not data.get("openid"):
        raise HTTPException(status_code=400, detail="openid is missing in wechat response")

    return {
        "success": True,
        "data": {
            "openid": data["openid"],
            "session_key": data.get("session_key"),
            "unionid": data.get("unionid"),
        },
    }
