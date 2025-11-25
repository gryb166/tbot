from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3

app = FastAPI()

# Дозволяємо фронтенду з localhost отримувати дані
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

DB_FILE = "database.db"

def get_all_trades():
    """Повертає всі угоди з бази даних у вигляді списку словників"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM trades ORDER BY id ASC")
    rows = cur.fetchall()
    conn.close()
    trades = []
    for row in rows:
        trades.append({
            "id": row["id"],
            "side": row["side"],
            "result": row["result"],
            "entry_price": row["entry_price"],
            "exit_price": row["exit_price"],
            "change": row["change"],          # число від -1 до 1
            "timestamp": row["timestamp"]
        })
    return trades

@app.get("/trades")
def trades():
    """Повертає всі угоди у форматі, який очікує фронтенд"""
    rows = get_all_trades()
    result = []
    for t in rows:
        result.append({
            "id": t["id"],
            "side": t["side"],
            "result": t["result"],
            "entry_price": t["entry_price"],
            "exit_price": t["exit_price"],
            "change_pct": t["change"],       # фронтенд очікує change_pct
            "time": t["timestamp"]           # фронтенд очікує поле "time"
        })
    return result
