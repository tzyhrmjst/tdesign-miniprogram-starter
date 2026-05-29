from datetime import datetime, timedelta, timezone

from app.db.database import get_conn
from app.services.wechat_service import send_subscribe_message


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def row_to_alert(row):
    data = dict(row)
    data["enabled"] = bool(data["enabled"])
    return data


def list_alerts(openid: str):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM alert_rules WHERE openid = ? ORDER BY created_at DESC",
            (openid,),
        ).fetchall()
    return [row_to_alert(row) for row in rows]


def create_alert(payload: dict):
    created_at = now_iso()
    with get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT INTO alert_rules
            (openid, name, direction, target_price, unit, cooldown_minutes, enabled, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["openid"],
                payload["name"],
                payload["direction"],
                payload["target_price"],
                payload["unit"],
                payload.get("cooldown_minutes", 720),
                1 if payload.get("enabled", True) else 0,
                created_at,
                created_at,
            ),
        )
        row = conn.execute("SELECT * FROM alert_rules WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return row_to_alert(row)


def update_alert(rule_id: int, payload: dict):
    fields = ["name", "direction", "target_price", "unit", "cooldown_minutes", "enabled"]
    values = []
    assignments = []
    for field in fields:
        if field in payload:
            assignments.append(f"{field} = ?")
            values.append(1 if field == "enabled" and payload[field] else 0 if field == "enabled" else payload[field])
    assignments.append("updated_at = ?")
    values.append(now_iso())
    values.append(rule_id)
    with get_conn() as conn:
        conn.execute(f"UPDATE alert_rules SET {', '.join(assignments)} WHERE id = ?", values)
        row = conn.execute("SELECT * FROM alert_rules WHERE id = ?", (rule_id,)).fetchone()
    return row_to_alert(row)


def delete_alert(rule_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM alert_rules WHERE id = ?", (rule_id,))


def list_histories(openid: str):
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT h.*, r.name AS rule_name
            FROM alert_histories h
            LEFT JOIN alert_rules r ON r.id = h.rule_id
            WHERE h.openid = ?
            ORDER BY h.triggered_at DESC, h.id DESC
            """,
            (openid,),
        ).fetchall()
    return [dict(row) for row in rows]


def _cooldown_passed(last_triggered_at, cooldown_minutes):
    if not last_triggered_at:
        return True
    last = datetime.fromisoformat(last_triggered_at.replace("Z", "+00:00"))
    return datetime.now(timezone.utc) - last >= timedelta(minutes=cooldown_minutes)


def _format_local_time(value):
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt.astimezone(timezone(timedelta(hours=8))).strftime("%Y年%m月%d日 %H:%M")


def _build_subscribe_data(rule, current_price, triggered_at):
    unit_text = "人民币/克" if rule["unit"] == "cny_g" else "美元/盎司"
    direction_text = "高于" if rule["direction"] == "above" else "低于"
    return {
        "amount4": {"value": f"{current_price:.2f}"},
        "time5": {"value": _format_local_time(triggered_at)},
        "time11": {"value": _format_local_time(triggered_at)},
        "thing15": {"value": "国际黄金"},
        "thing6": {"value": f"已{direction_text}{rule['target_price']:.2f}{unit_text}"},
    }


def scan_alerts(price: dict):
    with get_conn() as conn:
        previous = conn.execute(
            "SELECT * FROM price_snapshots ORDER BY captured_at DESC, id DESC LIMIT 1 OFFSET 1"
        ).fetchone()
        rules = conn.execute("SELECT * FROM alert_rules WHERE enabled = 1").fetchall()

        triggered = []
        for rule in rules:
            current_price = price["price_cny_g"] if rule["unit"] == "cny_g" else price["price_usd_oz"]
            previous_price = None
            if previous:
                previous_price = previous["price_cny_g"] if rule["unit"] == "cny_g" else previous["price_usd_oz"]

            above_hit = rule["direction"] == "above" and current_price >= rule["target_price"]
            below_hit = rule["direction"] == "below" and current_price <= rule["target_price"]
            crossed = rule["last_triggered_at"] is None
            if previous_price is not None and rule["last_triggered_at"] is not None:
                crossed = (
                    rule["direction"] == "above"
                    and previous_price < rule["target_price"] <= current_price
                ) or (
                    rule["direction"] == "below"
                    and previous_price > rule["target_price"] >= current_price
                )
            if not (above_hit or below_hit) or not crossed:
                continue
            if not _cooldown_passed(rule["last_triggered_at"], rule["cooldown_minutes"]):
                continue

            triggered_at = now_iso()
            message = "黄金价格提醒已触发"
            conn.execute(
                """
                INSERT INTO alert_histories
                (rule_id, openid, trigger_price, target_price, direction, unit, message, triggered_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rule["id"],
                    rule["openid"],
                    current_price,
                    rule["target_price"],
                    rule["direction"],
                    rule["unit"],
                    message,
                    triggered_at,
                ),
            )
            conn.execute(
                "UPDATE alert_rules SET last_triggered_at = ?, updated_at = ? WHERE id = ?",
                (triggered_at, triggered_at, rule["id"]),
            )
            try:
                send_subscribe_message(
                    rule["openid"],
                    _build_subscribe_data(rule, current_price, triggered_at),
                )
            except Exception as exc:
                print(f"subscribe message failed for rule {rule['id']}: {exc}")
            triggered.append(rule["id"])
    return triggered
