"""
สคริปต์สำหรับดูข้อมูลในฐานข้อมูล
ใช้ดูและวิเคราะห์ผลการทำนายที่เก็บใน crypto_ai.db
"""
import sqlite3
from datetime import datetime

DB_PATH = "crypto_ai.db"

def view_predictions(limit=20):
    """แสดงผลการทำนายล่าสุด"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=" * 80)
    print("  📊 CRYPTO AI - PREDICTIONS DATABASE VIEWER")
    print("=" * 80)
    
    # ตรวจสอบว่าตารางมีอยู่หรือไม่
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='predictions'")
    if not cursor.fetchone():
        print("\n❌ Table 'predictions' does not exist!")
        print("   Please run db_reset.py or start the server to create the table.")
        conn.close()
        return
    
    # นับจำนวนข้อมูลทั้งหมด
    cursor.execute("SELECT COUNT(*) FROM predictions")
    total = cursor.fetchone()[0]
    print(f"\n📈 Total Records: {total}")
    
    if total == 0:
        print("\n⚠️  No predictions yet!")
        print("   Scheduler will save predictions when it runs:")
        print("   - First run: on server startup")
        print("   - Scheduled: every 30 mins (5m), every hour (1h), every 4 hours (4h)")
        conn.close()
        return
    
    # ดึงข้อมูลการทำนายล่าสุด
    cursor.execute(f"""
        SELECT * FROM predictions 
        ORDER BY created_at DESC 
        LIMIT {limit}
    """)
    rows = cursor.fetchall()
    
    print(f"\n📋 Recent {len(rows)} Predictions:\n")
    print("-" * 80)
    print(f"{'ID':<4} {'Coin':<6} {'TF':<4} {'Current Price':>14} {'Predicted':>14} {'Trend':<10} {'Time'}")
    print("-" * 80)
    
    for row in rows:
        # แปลง trend เป็นสัญลักษณ์
        trend_icon = "📈 Up" if row['trend'] == 'Uptrend' else "📉 Down"
        print(f"{row['id']:<4} {row['coin']:<6} {row['timeframe']:<4} "
              f"${row['current_price']:>12,.2f} ${row['predicted_price']:>12,.2f} "
              f"{trend_icon:<10} {row['created_at']}")
    
    print("-" * 80)
    
    # สถิติแยกตามเหรียญ
    print("\n📊 Statistics by Coin:")
    cursor.execute("""
        SELECT coin, 
               COUNT(*) as count,
               AVG(current_price) as avg_price,
               AVG(predicted_price) as avg_predicted
        FROM predictions 
        GROUP BY coin
    """)
    stats = cursor.fetchall()
    
    for stat in stats:
        print(f"   {stat['coin']}: {stat['count']} records, "
              f"Avg Price: ${stat['avg_price']:,.2f}, "
              f"Avg Predicted: ${stat['avg_predicted']:,.2f}")
    
    # สถิติแยกตาม Timeframe
    print("\n📊 Statistics by Timeframe:")
    cursor.execute("""
        SELECT timeframe, 
               COUNT(*) as count,
               SUM(CASE WHEN trend = 'Uptrend' THEN 1 ELSE 0 END) as uptrends,
               SUM(CASE WHEN trend = 'Downtrend' THEN 1 ELSE 0 END) as downtrends
        FROM predictions 
        GROUP BY timeframe
    """)
    tf_stats = cursor.fetchall()
    
    for stat in tf_stats:
        print(f"   {stat['timeframe']}: {stat['count']} records, "
              f"↑ {stat['uptrends']} Uptrends, ↓ {stat['downtrends']} Downtrends")
    
    conn.close()
    print("\n" + "=" * 80)


def view_table_structure():
    """แสดงโครงสร้างตาราง"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n📋 Table Structure (predictions):")
    cursor.execute("PRAGMA table_info(predictions)")
    cols = cursor.fetchall()
    
    for col in cols:
        required = 'NOT NULL' if col[3] else ''
        print(f"   {col[1]:<20} {col[2]:<10} {required}")
    
    conn.close()


if __name__ == "__main__":
    view_table_structure()
    view_predictions(limit=20)
