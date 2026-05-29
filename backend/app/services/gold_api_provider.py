import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

OUNCE_TO_GRAM = 31.1035
USD_CNY_RATE = float(os.getenv("USD_CNY_RATE", "7.2"))
SGE_SYMBOL = os.getenv("SGE_GOLD_SYMBOL", "Au99.99")
CHINA_TZ = timezone(timedelta(hours=8))
K780_APPKEY = os.getenv("K780_APPKEY", "10003")
K780_SIGN = os.getenv("K780_SIGN", "b59bc3ef6191eb9f747dd4e83c99f2a4")
K780_GOLD_ID = os.getenv("K780_GOLD_ID", "1051")
APIHZ_GOLD_CONTRACT = os.getenv("APIHZ_GOLD_CONTRACT", "Au(T+D)")
SALE_PREMIUM_CNY_G = float(os.getenv("SALE_PREMIUM_CNY_G", "0"))
BUYBACK_SPREAD_CNY_G = float(os.getenv("BUYBACK_SPREAD_CNY_G", "2.0"))


def _headers(referer: str) -> dict:
    return {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://www.sge.com.cn",
        "Referer": referer,
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
        ),
        "X-Requested-With": "XMLHttpRequest",
    }


class GoldApiProvider:
    jdjygold_url = "https://api.jdjygold.com/gw2/generic/jrm/h5/m/stdLatestPrice?productSku=1961543816"
    apihz_url = "https://cn.apihz.cn/api/jinrong/goldshnew.php?id=88888888&key=88888888"
    exchange_rate_url = "https://open.er-api.com/v6/latest/USD"
    k780_url = "https://sapi.k780.com/"
    quotation_url = "https://www.sge.com.cn/graph/quotations"
    daily_url = "https://www.sge.com.cn/graph/Dailyhq"
    fallback_url = "https://api.gold-api.com/price/XAU"

    def latest(self) -> dict:
        try:
            return self._latest_jdjygold()
        except Exception:
            pass

        try:
            return self._latest_sale_price()
        except Exception:
            pass

        try:
            return self._latest_apihz()
        except Exception:
            pass

        try:
            return self._latest_k780()
        except Exception:
            pass

        try:
            return self._latest_sge_quotation()
        except Exception:
            try:
                return self._latest_sge_daily()
            except Exception:
                return self._latest_international_fallback()

    def _latest_jdjygold(self) -> dict:
        with urllib.request.urlopen(self.jdjygold_url, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))

        result = payload.get("resultData", {})
        if result.get("status") != "SUCCESS":
            raise ValueError(result.get("errorMessage") or "JD gold API failed")

        datas = result["datas"]
        price_cny_g = float(datas["price"])
        change = float(datas["upAndDownAmt"])
        change_percent = float(datas["upAndDownRate"].replace("%", ""))

        ts_ms = int(datas["time"])
        updated_at = datetime.fromtimestamp(ts_ms / 1000, tz=CHINA_TZ).isoformat()

        price_usd_oz = round((price_cny_g * OUNCE_TO_GRAM) / USD_CNY_RATE, 2)
        buyback_price = round(price_cny_g - BUYBACK_SPREAD_CNY_G, 2)

        return {
            "symbol": "JDJY_GOLD",
            "price_usd_oz": price_usd_oz,
            "price_cny_g": price_cny_g,
            "change": change,
            "change_percent": change_percent,
            "updated_at": updated_at,
            "source": "京东金融黄金",
            "buyback_price_cny_g": buyback_price,
        }

    def _latest_sale_price(self) -> dict:
        international = self._fetch_international_xau()
        usd_cny_rate = self._fetch_usd_cny_rate()
        base_cny_g = (international["price_usd_oz"] * usd_cny_rate) / OUNCE_TO_GRAM
        sale_price = base_cny_g + SALE_PREMIUM_CNY_G
        previous_sale_price = self._previous_sale_price(sale_price)
        change = round(sale_price - previous_sale_price, 2)
        change_percent = round((change / previous_sale_price) * 100, 2) if previous_sale_price else 0
        return {
            "symbol": "SALE_XAU_CNY_G",
            "price_usd_oz": round(international["price_usd_oz"], 2),
            "price_cny_g": round(sale_price, 2),
            "change": change,
            "change_percent": change_percent,
            "updated_at": international["updated_at"],
            "source": "国际金价折算",
            "base_price_cny_g": round(base_cny_g, 2),
            "sale_premium_cny_g": round(SALE_PREMIUM_CNY_G, 2),
            "buyback_price_cny_g": round(sale_price - BUYBACK_SPREAD_CNY_G, 2),
            "usd_cny_rate": round(usd_cny_rate, 6),
        }

    def _fetch_international_xau(self) -> dict:
        with urllib.request.urlopen(self.fallback_url, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return {
            "price_usd_oz": float(payload["price"]),
            "updated_at": payload.get("updatedAt") or datetime.now(timezone.utc).isoformat(),
        }

    def _fetch_usd_cny_rate(self) -> float:
        with urllib.request.urlopen(self.exchange_rate_url, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
        rate = payload.get("rates", {}).get("CNY")
        if not rate:
            raise ValueError("missing USD/CNY rate")
        return float(rate)

    def _previous_sale_price(self, current_sale_price: float) -> float:
        return current_sale_price

    def _latest_k780(self) -> dict:
        params = urllib.parse.urlencode(
            {
                "app": "finance.gold_price",
                "goldid": K780_GOLD_ID,
                "appkey": K780_APPKEY,
                "sign": K780_SIGN,
                "format": "json",
            }
        )
        with urllib.request.urlopen(f"{self.k780_url}?{params}", timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))

        if payload.get("success") != "1":
            raise ValueError(payload.get("msg") or "K780 gold price request failed")

        item = payload["result"]["dtList"][K780_GOLD_ID]
        price_cny_g = float(item["last_price"])
        previous_cny_g = float(item.get("yesy_price") or price_cny_g)
        updated_at = datetime.strptime(item["uptime"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=CHINA_TZ).isoformat()
        source_name = item.get("varietynm") or item.get("variety") or K780_GOLD_ID
        price = self._normalize_sge_price(
            price_cny_g,
            previous_cny_g,
            updated_at,
            f"K780/NowAPI {source_name}",
        )
        price["symbol"] = item.get("variety") or source_name
        return price

    def _latest_apihz(self) -> dict:
        with urllib.request.urlopen(self.apihz_url, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))

        if payload.get("code") != 200:
            raise ValueError(payload.get("msg") or "APIHZ gold price request failed")

        target = None
        for item in payload.get("data", []):
            if item.get("合约") == APIHZ_GOLD_CONTRACT:
                target = item
                break
        if not target:
            raise ValueError(f"missing APIHZ contract: {APIHZ_GOLD_CONTRACT}")

        price_cny_g = float(target["最新价"])
        open_cny_g = float(target.get("开盘价") or price_cny_g)
        date_text = payload.get("date", "")
        updated_at = self._parse_apihz_date(date_text)
        price = self._normalize_sge_price(
            price_cny_g,
            open_cny_g,
            updated_at,
            f"接口盒子上金所延时行情 {APIHZ_GOLD_CONTRACT}",
        )
        price["symbol"] = APIHZ_GOLD_CONTRACT
        return price

    def _parse_apihz_date(self, date_text: str) -> str:
        try:
            date_value = datetime.strptime(date_text, "%Y年%m月%d日").date()
        except ValueError:
            date_value = datetime.now(CHINA_TZ).date()
        return datetime.combine(date_value, datetime.now(CHINA_TZ).time(), tzinfo=CHINA_TZ).isoformat()

    def _post_json(self, url: str, referer: str) -> dict:
        data = urllib.parse.urlencode({"instid": SGE_SYMBOL}).encode("utf-8")
        request = urllib.request.Request(url, data=data, headers=_headers(referer), method="POST")
        with urllib.request.urlopen(request, timeout=8) as response:
            return json.loads(response.read().decode("utf-8"))

    def _latest_sge_quotation(self) -> dict:
        payload = self._post_json(self.quotation_url, "https://www.sge.com.cn/")
        points = [
            (time_text, float(price))
            for time_text, price in zip(payload.get("times", []), payload.get("data", []))
            if price not in (None, "", "-")
        ]
        if not points:
            raise ValueError("empty SGE quotation payload")

        latest_time, latest_price = points[-1]
        previous_price = points[-2][1] if len(points) > 1 else latest_price
        updated_at = self._quotation_updated_at(payload, latest_time)
        return self._normalize_sge_price(
            latest_price,
            previous_price,
            updated_at,
            "上海黄金交易所 Au99.99 延时行情",
        )

    def _quotation_updated_at(self, payload: dict, latest_time: str) -> str:
        delay_text = payload.get("delaystr") or payload.get("delayStr") or ""
        date_text = delay_text.split()[0] if delay_text else datetime.now(CHINA_TZ).date().isoformat()
        return datetime.fromisoformat(f"{date_text}T{latest_time}:00+08:00").isoformat()

    def _latest_sge_daily(self) -> dict:
        payload = self._post_json(self.daily_url, "https://www.sge.com.cn/sjzx/mrhq")
        rows = payload.get("time", [])
        if not rows:
            raise ValueError("empty SGE daily payload")

        latest = rows[-1]
        previous = rows[-2] if len(rows) > 1 else latest
        latest_price = float(latest[2])
        previous_price = float(previous[2])
        updated_at = datetime.fromisoformat(f"{latest[0]}T15:30:00+08:00").isoformat()
        return self._normalize_sge_price(
            latest_price,
            previous_price,
            updated_at,
            "上海黄金交易所 Au99.99 日行情",
        )

    def _normalize_sge_price(self, price_cny_g: float, previous_cny_g: float, updated_at: str, source: str) -> dict:
        change = round(price_cny_g - previous_cny_g, 2)
        change_percent = round((change / previous_cny_g) * 100, 2) if previous_cny_g else 0
        return {
            "symbol": SGE_SYMBOL,
            "price_usd_oz": round((price_cny_g * OUNCE_TO_GRAM) / USD_CNY_RATE, 2),
            "price_cny_g": round(price_cny_g, 2),
            "change": change,
            "change_percent": change_percent,
            "updated_at": updated_at,
            "source": source,
        }

    def _latest_international_fallback(self) -> dict:
        with urllib.request.urlopen(self.fallback_url, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))

        price = float(payload["price"])
        updated_at = payload.get("updatedAt") or datetime.now(timezone.utc).isoformat()
        return {
            "symbol": payload.get("symbol", "XAU"),
            "price_usd_oz": price,
            "price_cny_g": round((price * USD_CNY_RATE) / OUNCE_TO_GRAM, 2),
            "change": 0,
            "change_percent": 0,
            "updated_at": updated_at,
            "source": "gold-api.com",
        }
