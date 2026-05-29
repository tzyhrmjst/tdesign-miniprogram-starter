import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "gold.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS price_snapshots (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              symbol TEXT NOT NULL,
              price_usd_oz REAL NOT NULL,
              price_cny_g REAL NOT NULL,
              change_value REAL DEFAULT 0,
              change_percent REAL DEFAULT 0,
              source TEXT NOT NULL,
              captured_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS alert_rules (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              openid TEXT NOT NULL,
              name TEXT NOT NULL,
              direction TEXT NOT NULL CHECK(direction IN ('above', 'below')),
              target_price REAL NOT NULL,
              unit TEXT NOT NULL CHECK(unit IN ('usd_oz', 'cny_g')),
              cooldown_minutes INTEGER NOT NULL DEFAULT 720,
              enabled INTEGER NOT NULL DEFAULT 1,
              last_triggered_at TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS alert_histories (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              rule_id INTEGER NOT NULL,
              openid TEXT NOT NULL,
              trigger_price REAL NOT NULL,
              target_price REAL NOT NULL,
              direction TEXT NOT NULL,
              unit TEXT NOT NULL,
              message TEXT NOT NULL,
              triggered_at TEXT NOT NULL
            );
            """
        )
