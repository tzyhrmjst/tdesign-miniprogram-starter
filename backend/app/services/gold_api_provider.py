import json
import gzip
import os
import re
import urllib.request
from base64 import b64decode
from datetime import datetime, timedelta, timezone
from html import unescape
from urllib.parse import urlencode

CHINA_TZ = timezone(timedelta(hours=8))
XWTEAM_GOLD_URL = os.getenv("XWTEAM_GOLD_URL", "https://free.xwteam.cn/api/gold/trade?line=yt")
PULSEDATA_BASE_URL = os.getenv("PULSEDATA_BASE_URL", "http://39.107.99.235:1008").rstrip("/")
PULSEDATA_CODE = os.getenv("PULSEDATA_CODE", "RT_AU")
PULSEDATA_PUBLIC_FALLBACK = os.getenv("PULSEDATA_PUBLIC_FALLBACK", "true").lower() != "false"

GROUP_ID = os.getenv("GOLD_PRICE_GROUP_ID", "LF")
SYMBOL = os.getenv("GOLD_PRICE_SYMBOL", "AU")

OUNCE_TO_GRAM = 31.1035
USD_CNY_RATE = float(os.getenv("USD_CNY_RATE", "7.2"))


class GoldApiProvider:

    def latest(self) -> dict:
        try:
            return self._latest_xwteam()
        except Exception:
            return self._latest_pulsedata()

    def _latest_pulsedata(self) -> dict:
        try:
            return self._latest_pulsedata_quote()
        except Exception:
            if not PULSEDATA_PUBLIC_FALLBACK:
                raise
            return self._latest_pulsedata_public_page()

    def _latest_pulsedata_quote(self) -> dict:
        url = f"{PULSEDATA_BASE_URL}/getQuote.php?{urlencode({'code': PULSEDATA_CODE})}"
        payload = self._request_json(url)

        if payload.get("code") != 200:
            raise ValueError(payload.get("msg") or "PulseData quote request failed")

        target = self._extract_pulsedata_quote(payload.get("body") or payload.get("data"))
        if not target:
            raise ValueError(f"missing PulseData {PULSEDATA_CODE} price")
        return self._normalize_pulsedata_quote(target)

    def _latest_pulsedata_public_page(self) -> dict:
        html = self._request_text(f"{PULSEDATA_BASE_URL}/market/rtj.php")
        row_match = re.search(rf"<tr class='option_{re.escape(PULSEDATA_CODE)}'>(.*?)</tr>", html, re.S)
        if not row_match:
            raise ValueError(f"missing PulseData public row {PULSEDATA_CODE}")

        row = row_match.group(1)
        target = {
            "StockCode": PULSEDATA_CODE,
            "BP": self._extract_svg_price(row, "BP"),
            "SP": self._extract_svg_price(row, "SP"),
            "High": self._extract_cell_text(row, "High"),
            "Low": self._extract_cell_text(row, "Low"),
            "Time": self._extract_cell_text(row, "UpdateTime"),
        }
        return self._normalize_pulsedata_quote(target)

    def _request_json(self, url: str) -> dict:
        return json.loads(self._request_text(url))

    def _request_text(self, url: str) -> str:
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json,text/html,*/*",
                "Accept-Encoding": "gzip",
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
                ),
            },
        )
        with urllib.request.urlopen(request, timeout=8) as response:
            body = response.read()
            if response.headers.get("Content-Encoding") == "gzip":
                body = gzip.decompress(body)
            return body.decode("utf-8")

    def _extract_pulsedata_quote(self, data):
        if isinstance(data, list):
            for item in data:
                if str(item.get("StockCode") or item.get("code") or "").upper() == PULSEDATA_CODE.upper():
                    return item
            return data[0] if data else None
        if isinstance(data, dict):
            if str(data.get("StockCode") or data.get("code") or "").upper() == PULSEDATA_CODE.upper():
                return data
            for key, value in data.items():
                if str(key).upper() == PULSEDATA_CODE.upper() and isinstance(value, dict):
                    return value
            for value in data.values():
                if isinstance(value, dict) and str(value.get("StockCode") or value.get("code") or "").upper() == PULSEDATA_CODE.upper():
                    return value
        return None

    def _normalize_pulsedata_quote(self, data: dict) -> dict:
        sale_price = self._number(data.get("SP") or data.get("SP1") or data.get("Sell") or data.get("Price"))
        buyback_price = self._number(data.get("BP") or data.get("BP1") or data.get("Buy") or data.get("Price") or sale_price)
        if not sale_price:
            raise ValueError(f"missing PulseData {PULSEDATA_CODE} sale price")

        updated_at = self._parse_china_time(data.get("Time") or data.get("UpdateTime"))
        return {
            "symbol": data.get("StockCode") or data.get("code") or PULSEDATA_CODE,
            "price_usd_oz": round((sale_price * OUNCE_TO_GRAM) / USD_CNY_RATE, 2),
            "price_cny_g": round(sale_price, 2),
            "change": self._number(data.get("Diff"), 0),
            "change_percent": self._number(data.get("DiffRate"), 0),
            "updated_at": updated_at,
            "source": "脉动行情",
            "buyback_price_cny_g": round(buyback_price, 2),
            "high_price_cny_g": self._number(data.get("High"), 0),
            "low_price_cny_g": self._number(data.get("Low"), 0),
        }

    def _extract_cell_text(self, row: str, field: str) -> str:
        cell_match = re.search(rf"id='{re.escape(field)}_{re.escape(PULSEDATA_CODE)}'[^>]*>(.*?)</td>", row, re.S)
        if not cell_match:
            return ""
        return unescape(re.sub("<.*?>", "", cell_match.group(1))).strip()

    def _extract_svg_price(self, row: str, field: str) -> str:
        image_match = re.search(
            rf"id='{re.escape(field)}_{re.escape(PULSEDATA_CODE)}'.*?src='data:image/svg\+xml;base64,([^']+)'",
            row,
            re.S,
        )
        if not image_match:
            return self._extract_cell_text(row, field)
        svg = b64decode(image_match.group(1)).decode("utf-8", "ignore")
        return "".join(unescape(text) for text in re.findall(r"<text[^>]*>(.*?)</text>", svg))

    def _parse_china_time(self, value):
        if not value:
            return datetime.now(CHINA_TZ).isoformat()
        try:
            return datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S").replace(tzinfo=CHINA_TZ).isoformat()
        except ValueError:
            return str(value)

    def _number(self, value, default=None):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _latest_xwteam(self) -> dict:
        payload = self._request_json(XWTEAM_GOLD_URL)

        if payload.get("code") != 200:
            raise ValueError(payload.get("msg") or "XWTeam gold request failed")

        data = payload.get("data") or {}
        target = None
        for item in data.get(GROUP_ID, []):
            if str(item.get("Symbol", "")).upper() == SYMBOL.upper():
                target = item
                break
        if not target:
            raise ValueError(f"missing {GROUP_ID} {SYMBOL} price")

        sale_price = float(target["SP"])
        buyback_price = float(target["BP"])
        updated_at = datetime.strptime(data["UpTime"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=CHINA_TZ).isoformat()

        return {
            "symbol": target.get("Symbol", SYMBOL),
            "price_usd_oz": round((sale_price * OUNCE_TO_GRAM) / USD_CNY_RATE, 2),
            "price_cny_g": round(sale_price, 2),
            "change": 0,
            "change_percent": 0,
            "updated_at": updated_at,
            "source": "福利云",
            "buyback_price_cny_g": round(buyback_price, 2),
            "high_price_cny_g": float(target.get("High", 0) or 0),
            "low_price_cny_g": float(target.get("Low", 0) or 0),
            "open_mark": data.get("OpenMark"),
        }
