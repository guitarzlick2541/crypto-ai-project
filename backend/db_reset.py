"""
สคริปต์สำหรับรีเซ็ตฐานข้อมูล
ลบตารางเก่าและสร้างตาราง predictions ใหม่ด้วยโครงสร้างที่ถูกต้อง
"""
import sqlite3
import os

# ใช้ absolute path จากตำแหน่งของไฟล์นี้เสมอ เพื่อความชัวร์
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(CURRENT_DIR, "crypto_ai.db")

print("=" * 50)
print("  🔄 Database Reset Script")
print("=" * 50)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ตรวจสอบโครงสร้างปัจจุบัน
print("\n[1] Checking current table structure...")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='predictions'")
if cursor.fetchone():
    cursor.execute("PRAGMA table_info(predictions)")
    cols = cursor.fetchall()
    print("    Current columns:")
    for col in cols:
        print(f"      - {col[1]} ({col[2]})")
    
    # ลบตารางเก่า
    print("\n[2] Dropping old table...")
    cursor.execute("DROP TABLE predictions")
    print("    ✓ Old table dropped")
else:
    print("    Table does not exist - creating new one")

# สร้างตารางใหม่ด้วยโครงสร้างที่ถูกต้อง
print("\n[3] Creating new table...")
cursor.execute("""
    CREATE TABLE predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        coin TEXT NOT NULL,
        timeframe TEXT NOT NULL,
        current_price REAL NOT NULL,
        predicted_price REAL NOT NULL,
        trend TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")
conn.commit()
print("    ✓ New table created")

# ตรวจสอบโครงสร้างใหม่
print("\n[4] Verifying new structure...")
cursor.execute("PRAGMA table_info(predictions)")
cols = cursor.fetchall()
print("    New columns:")
for col in cols:
    print(f"      - {col[1]} ({col[2]})")

conn.close()

print("\n" + "=" * 50)
print("  ✓ Database reset complete!")
print("=" * 50)
