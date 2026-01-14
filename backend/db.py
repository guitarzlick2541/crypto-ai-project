import sqlite3
import logging

# ตั้งค่า Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db")

def get_db():
    """เชื่อมต่อฐานข้อมูล"""
    conn = sqlite3.connect("crypto_ai.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """เริ่มต้นตารางฐานข้อมูล"""
    conn = get_db()
    cur = conn.cursor()
    
    # สร้างตาราง predictions หากยังไม่มี
    cur.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            coin TEXT,
            timeframe TEXT,
            current_price REAL,
            predicted_price REAL,
            trend TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

def save_prediction(coin, timeframe, current, predicted, trend):
    """บันทึกผลการทำนายลงฐานข้อมูล"""
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO predictions (coin, timeframe, current_price, predicted_price, trend)
            VALUES (?, ?, ?, ?, ?)
        """, (coin, timeframe, current, predicted, trend))
        conn.commit()
        logger.info(f"Saved prediction for {coin} {timeframe}")
    except Exception as e:
        logger.error(f"Error saving prediction: {e}")
    finally:
        conn.close()
