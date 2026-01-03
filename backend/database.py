import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect("predictions.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            actual REAL,
            predicted REAL,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_prediction(symbol, actual, predicted):
    conn = sqlite3.connect("predictions.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO predictions VALUES (NULL, ?, ?, ?, ?)",
        (symbol, actual, predicted, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def get_history():
    conn = sqlite3.connect("predictions.db")
    c = conn.cursor()
    rows = c.execute(
        "SELECT symbol, actual, predicted, created_at FROM predictions ORDER BY created_at DESC LIMIT 100"
    ).fetchall()
    conn.close()
    return rows
