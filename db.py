import sqlite3
from datetime import datetime

DB_PATH = "database.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            side TEXT,
            result TEXT,
            entry_price REAL,
            exit_price REAL,
            change REAL,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_trade(side, result, entry_price, exit_price, change):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO trades (side, result, entry_price, exit_price, change, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (side, result, entry_price, exit_price, change, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def get_all_trades(limit=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if limit:
        c.execute("SELECT * FROM trades ORDER BY timestamp DESC LIMIT ?", (limit,))
    else:
        c.execute("SELECT * FROM trades ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()
    return rows
