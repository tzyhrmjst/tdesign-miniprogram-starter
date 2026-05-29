import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from fastapi import HTTPException


ACCESS_TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
SUBSCRIBE_SEND_URL = "https://api.weixin.qq.com/cgi-bin/message/subscribe/send"

_access_token = ""
_access_token_expires_at = 0


def _request_json(url, payload=None):
    data = None
    headers = {}
    if payload is not None:
        import json

        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method="POST" if payload is not None else "GET")
    with urllib.request.urlopen(request, timeout=10) as response:
        import json

        return json.loads(response.read().decode("utf-8"))


def get_access_token():
    global _access_token, _access_token_expires_at
    now = datetime.now(timezone.utc).timestamp()
    if _access_token and now < _access_token_expires_at:
        return _access_token

    appid = os.getenv("WECHAT_APPID")
    secret = os.getenv("WECHAT_SECRET")
    if not appid or not secret:
        raise HTTPException(status_code=503, detail="WeChat credentials are not configured")

    query = urllib.parse.urlencode(
        {
            "grant_type": "client_credential",
            "appid": appid,
            "secret": secret,
        }
    )
    data = _request_json(f"{ACCESS_TOKEN_URL}?{query}")
    token = data.get("access_token")
    if not token:
        raise HTTPException(status_code=502, detail=data)

    _access_token = token
    _access_token_expires_at = now + int(data.get("expires_in", 7200)) - 300
    return _access_token


def send_subscribe_message(openid: str, data: dict):
    template_id = os.getenv("WECHAT_SUBSCRIBE_TEMPLATE_ID")
    if not template_id:
        return {"skipped": True, "reason": "template id is not configured"}

    access_token = get_access_token()
    payload = {
        "touser": openid,
        "template_id": template_id,
        "page": "pages/history/index",
        "miniprogram_state": os.getenv("WECHAT_MINIPROGRAM_STATE", "developer"),
        "lang": "zh_CN",
        "data": data,
    }
    result = _request_json(f"{SUBSCRIBE_SEND_URL}?access_token={access_token}", payload)
    if result.get("errcode"):
        raise HTTPException(status_code=502, detail=result)
    return result
