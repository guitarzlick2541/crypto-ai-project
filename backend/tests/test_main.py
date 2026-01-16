import sys
import os
from fastapi.testclient import TestClient
import pytest
from unittest.mock import patch

# Add backend directory to sys.path so we can import 'main'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)

def test_read_root():
    """ทดสอบหน้าแรก (Health Check)"""
    response = client.get("/")
    assert response.status_code == 200
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
    response = client.get("/timeframes")
    assert response.status_code == 200
    data = response.json()
    assert "timeframes" in data
    assert "1h" in data["timeframes"]
    assert "5m" in data["timeframes"]

def test_history_endpoint_validation():
    """ทดสอบว่า History API ทำงานเมื่อไม่ส่งพารามิเตอร์ (ใช้ Default)"""
    response = client.get("/history")
    assert response.status_code == 200
    data = response.json()
    assert "prices" in data
    assert "times" in data 

# ============================================================================
# New API Tests added below
# ============================================================================

@patch("main.predict_with_history")
def test_predict_endpoint(mock_predict):
    """ทดสอบ API ทำนายราคา (/predict)"""
    # จำลองผลลัพธ์จาก ai_engine
    mock_predict.return_value = {
        "current": 50000.0,
        "predicted": 50500.0,
        "times": ["10:00", "11:00"],
        "actual_prices": [49000.0, 50000.0],
        "predicted_prices": [49100.0, 50500.0]
    }
    
    response = client.get("/predict?coin=BTC&timeframe=1h")
    assert response.status_code == 200
    data = response.json()
    
    assert data["coin"] == "BTC"
    assert data["current"] == 50000.0
    assert data["predicted"] == 50500.0
    assert "times" in data

@patch("main.backtest")
def test_backtest_endpoint(mock_backtest):
    """ทดสอบ API Backtest (/backtest)"""
    # จำลองผลลัพธ์ (MAE, RMSE)
    mock_backtest.return_value = (100.5, 150.2)
    
    response = client.get("/backtest?coin=BTC&timeframe=1h")
    assert response.status_code == 200
    data = response.json()
    
    assert data["mae"] == 100.5
    assert data["rmse"] == 150.2

@patch("main.backtest")
@patch("main.predict_price")
def test_performance_endpoint(mock_predict, mock_backtest):
    """ทดสอบ API Performance สำหรับ Dashboard"""
    # จำลองผลลัพธ์
    mock_backtest.return_value = (50.0, 70.0)
    mock_predict.return_value = (1000.0, 1010.0) # current, predicted
    
    response = client.get("/performance?coin=BTC")
    assert response.status_code == 200
    data = response.json()
    
    assert "performance" in data
    assert "5m" in data["performance"]
    assert "1h" in data["performance"]
    # ตรวจสอบว่ามีค่า Key Metrics ครบ
    assert "accuracy" in data["performance"]["1h"]

@patch("main.subprocess.run")
@patch("main.load_specific_model")
def test_retrain_endpoint(mock_load, mock_subprocess):
    """ทดสอบ API Retrain (Mock การรัน Script จริง)"""
    # จำลองว่ารัน subprocess สำเร็จ
    mock_subprocess.return_value.stdout = "Training complete... Loss: 0.001"
    
    response = client.post("/retrain?timeframe=1h")
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "success"
    assert "retrained" in data["message"]
    # ตรวจสอบว่ามีการเรียกโหลดโมเดลใหม่จริง
    mock_load.assert_called_with("1h")
