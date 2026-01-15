import sys
import os
import pytest
import pandas as pd
import numpy as np
import sqlite3
from unittest.mock import MagicMock, patch

# เพิ่ม path ให้ import backend modules ได้
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_service import get_training_data
from ai_engine import predict_price, FEATURE_COLUMNS, WINDOW
import db

# ============================================================================
# 1. Test Data Loader & Feature Engineering
# ============================================================================
@patch('data_service.requests.get')
def test_data_loader_and_features(mock_get):
    """
    ทดสอบการดึงข้อมูลและคำนวณ Features (RSI, MACD, etc.)
    """
    # จำลองข้อมูลจาก Binance API (30 แท่งเทียน)
    mock_data = []
    base_price = 50000.0
    for i in range(100):
        mock_data.append([
            1609459200000 + (i * 3600000), # Time
            str(base_price), # Open
            str(base_price + 100), # High
            str(base_price - 100), # Low
            str(base_price + 50), # Close
            "100.0", # Volume
            1609459200000 + ((i+1) * 3600000),
            "5000000.0", 100, "50.0", "2500000.0", "0"
        ])
        base_price += 10 # ราคาขึ้นเรื่อยๆ
        
    mock_get.return_value.json.return_value = mock_data

    # เรียกฟังก์ชันจริง
    df, features = get_training_data(symbol="BTCUSDT", interval="1h", limit=100)

    # ตรวจสอบ 1: ได้ข้อมูลกลับมาหรือไม่
    assert not df.empty
    assert len(df) > 0
    
    # ตรวจสอบ 2: มี Columns ครบตามที่ AI ต้องการหรือไม่
    expected_columns = ["close", "rsi", "macd", "ma_5", "volatility", "time"]
    for col in expected_columns:
        assert col in df.columns, f"Missing column: {col}"
        
    # ตรวจสอบ 3: Feature Engineering ทำงานถูกต้อง (ค่าไม่เป็น NaN ในแถวท้ายๆ)
    assert not np.isnan(df.iloc[-1]["rsi"])
    assert not np.isnan(df.iloc[-1]["macd"])

# ============================================================================
# 2. Test AI Model Prediction (Logic only)
# ============================================================================

@patch('ai_engine.models', {}) # Mock models ให้ว่างเปล่า (จำลองว่ายังไม่ได้โหลด)
@patch('data_service.requests.get')
def test_prediction_fallback_logic(mock_get):
    """
    ทดสอบว่าถ้าไม่มีโมเดล ระบบต้อง Fallback ไปใช้ราคาปัจจุบันได้โดยไม่ Error
    """
    # จำลองข้อมูล (ราคาต้องขยับเพื่อให้ RSI คำนวณได้)
    mock_data = []
    price = 50000.0
    for i in range(200):
        price += 10 if i % 2 == 0 else -5 # ขยับขึ้นลง
        mock_data.append([
            1609459200000 + (i * 3600000), 
            str(price), str(price+100), str(price-100), str(price+50), 
            "100"
        ] + ["0"]*6)
        
    mock_get.return_value.json.return_value = mock_data

    # เรียกทำนาย
    current, predicted = predict_price("BTCUSDT", "1h")

    # ต้องไม่ Error และค่าต้องเท่ากัน (Fallback logic)
    assert isinstance(current, float)
    assert isinstance(predicted, float)
    assert current == predicted
    # ค่าปัจจุบันคือราคา close สุดท้าย (price + 50)
    expected_price = price + 50
    assert current == expected_price

# ============================================================================
# 3. Test Database Operations
# ============================================================================
class ConnectionWrapper:
    """Wrapper เพื่อดักจับคำสั่ง close ไม่ให้ปิด connection จริง"""
    def __init__(self, real_conn):
        self.real_conn = real_conn
    
    def close(self):
        # ไม่ทำอะไร (ดักจับคำสั่งปิด)
        pass
        
    def __getattr__(self, name):
        # ส่งต่อคำสั่งอื่นๆ ไปยัง connection จริง
        return getattr(self.real_conn, name)

class TestDatabase:
    def setup_method(self):
        """สร้าง In-memory DB สำหรับทดสอบ"""
        # สร้าง connection จริง
        self.real_conn = sqlite3.connect(':memory:')
        self.real_conn.row_factory = sqlite3.Row
        
        # สร้าง Wrapper
        self.wrapped_conn = ConnectionWrapper(self.real_conn)
        
        # Override ฟังก์ชัน get_db ให้คืนค่า Wrapper แทน
        self.original_get_db = db.get_db
        db.get_db = lambda: self.wrapped_conn

        # สร้างตาราง (ใช้ connection จริงหรือ wrapper ก็ได้ผลเหมือนกัน)
        db.init_db()

    def teardown_method(self):
        """คืนค่าเดิมและปิด connection"""
        db.get_db = self.original_get_db
        # ปิด connection จริงๆ ที่นี่
        self.real_conn.close()

    def test_save_prediction(self):
        """ทดสอบการบันทึกข้อมูลลง DB"""
        # บันทึกข้อมูลทดสอบ
        db.save_prediction(
            coin="BTC",
            timeframe="1h",
            current=50000.0,
            predicted=51000.0,
            trend="Uptrend"
        )

        # อ่านข้อมูลกลับมาตรวจสอบ
        cursor = self.real_conn.cursor()
        cursor.execute("SELECT * FROM predictions WHERE coin='BTC'")
        row = cursor.fetchone()

        assert row is not None
        assert row["coin"] == "BTC"
        assert row["timeframe"] == "1h"
        assert row["current_price"] == 50000.0
        assert row["predicted_price"] == 51000.0
        assert row["trend"] == "Uptrend"
