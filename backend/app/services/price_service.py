from collections import defaultdict
from datetime import datetime, timedelta, timezone

from app.db.database import get_conn
from app.services.gold_api_provider import GoldApiProvider

provider = GoldApiProvider()


def _parse_ts(raw):
    """Parse captured_at to datetime, handling both +08:00 and Z suffix formats."""
    raw = raw.strip().replace("Z", "+00:00")
    return datetime.fromisoformat(raw)


def _now():
    return datetime.now(timezone.utc).isoformat()


def save_snapshot(price: dict):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO price_snapshots
            (symbol, price_usd_oz, price_cny_g, buyback_price_cny_g, change_value, change_percent, source, captured_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                price["symbol"],
                price["price_usd_oz"],
                price["price_cny_g"],
                price.get("buyback_price_cny_g") or price["price_cny_g"],
                price.get("change", 0),
                price.get("change_percent", 0),
                price["source"],
                price.get("updated_at") or _now(),
            ),
        )


def get_latest_price():
    try:
        price = provider.latest()
        save_snapshot(price)
        return price
    except Exception:
        with get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM price_snapshots ORDER BY captured_at DESC, id DESC LIMIT 1"
            ).fetchone()
        if not row:
            raise
        return {
            "symbol": row["symbol"],
            "price_usd_oz": row["price_usd_oz"],
            "price_cny_g": row["price_cny_g"],
            "buyback_price_cny_g": row["buyback_price_cny_g"] or row["price_cny_g"],
            "change": row["change_value"],
            "change_percent": row["change_percent"],
            "updated_at": row["captured_at"],
            "source": row["source"],
        }


def get_history(limit=288):
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT captured_at AS ts, price_usd_oz, price_cny_g
            FROM price_snapshots
            ORDER BY captured_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_kline(period_minutes=15, limit=96, price_type="sale"):
    """Return OHLC candles from snapshots within the exact time window, newest first in result.

    price_type: 'sale' uses price_cny_g, 'buyback' uses buyback_price_cny_g.
    """
    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=period_minutes * limit)
    price_column = "buyback_price_cny_g" if price_type == "buyback" else "price_cny_g"

    with get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT {price_column} AS price, captured_at
            FROM price_snapshots
            WHERE captured_at >= ?
            ORDER BY captured_at ASC, id ASC
            """,
            (start.isoformat(),),
        ).fetchall()

    buckets = defaultdict(list)
    for row in rows:
        ts = _parse_ts(row["captured_at"])
        bucket_minute = (ts.minute // period_minutes) * period_minutes
        bucket = ts.replace(minute=bucket_minute, second=0, microsecond=0)
        buckets[bucket.isoformat()].append(float(row["price"]))

    candles = []
    for bucket in sorted(buckets.keys()):
        prices = buckets[bucket]
        candles.append({
            "ts": bucket,
            "open": round(prices[0], 2),
            "close": round(prices[-1], 2),
            "high": round(max(prices), 2),
            "low": round(min(prices), 2),
        })

    return candles[-limit:]
