from datetime import datetime, timezone

from app.db.database import get_conn
from app.services.gold_api_provider import GoldApiProvider

provider = GoldApiProvider()


def _now():
    return datetime.now(timezone.utc).isoformat()


def save_snapshot(price: dict):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO price_snapshots
            (symbol, price_usd_oz, price_cny_g, change_value, change_percent, source, captured_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                price["symbol"],
                price["price_usd_oz"],
                price["price_cny_g"],
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
