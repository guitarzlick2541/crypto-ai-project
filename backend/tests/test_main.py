import sys
import os
from fastapi.testclient import TestClient
import pytest

# Add backend directory to sys.path so we can import 'main'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)

def test_read_root():
    """ทดสอบหน้าแรก (Health Check)"""
    response = client.get("/")
    assert response.status_code == 200
    # ปรับ Assert ให้ตรงกับที่ API ตอบกลับมาจริง
    assert "status" in response.json()
    assert response.json()["status"] == "CryptoAI API Running"

def test_get_coins():
    """ทดสอบ API ดึงรายชื่อเหรียญ"""
    response = client.get("/coins")
    assert response.status_code == 200
    data = response.json()
    assert "coins" in data
    assert "BTC" in data["coins"]
    assert "ETH" in data["coins"]

def test_get_timeframes():
    """ทดสอบ API ดึง Timeframes"""
    response = client.get("/timeframes")  # แก้จาก /api/timeframes
    assert response.status_code == 200
    data = response.json()
    assert "timeframes" in data
    assert "1h" in data["timeframes"]
    assert "5m" in data["timeframes"]

def test_history_endpoint_validation():
    """ทดสอบว่า History API ทำงานเมื่อไม่ส่งพารามิเตอร์ (ใช้ Default)"""
    # กรณีไม่ส่งพารามิเตอร์ใดๆ (จะใช้ Default: BTC, 1h, 50)
    response = client.get("/history")
    assert response.status_code == 200
    data = response.json()
    assert "prices" in data
    assert "times" in data 
