"""
AI Engine สำหรับทำนายราคาคริปโต
ใช้ Multi-Feature Input พร้อม Dynamic Scaling สำหรับแต่ละเหรียญ
Features: close, open, high, low, volume, price_change, volatility,
          ma_5, ma_10, ma_20, macd, rsi, bb_position, volume_change, price_position
"""

import numpy as np
import joblib
import os
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
from data_service import get_training_data, get_klines
from datetime import datetime, timedelta

# ค่า Window size สำหรับการทำนาย (ต้องตรงกับตอน training)
WINDOW = 20

# รายการ Features ที่ใช้ (ต้องตรงกับตอน training)
FEATURE_COLUMNS = [
    "close", "open", "high", "low", "volume",
    "price_change", "volatility",
    "ma_5", "ma_10", "ma_20",
    "macd", "rsi", "bb_position",
    "volume_change", "price_position"
]

# โหลดโมเดลและ Scaler สำหรับแต่ละ timeframe
print("Loading AI models and scalers...")
models = {}
scalers = {}

for tf in ["5m", "1h", "4h"]:
    # โหลดโมเดล
    model_path = f"../models/lstm_{tf}.h5"
    scaler_path = f"../models/scaler_{tf}.pkl"
    
    try:
        if os.path.exists(model_path):
            models[tf] = load_model(model_path, compile=False)
            print(f"  ✓ Loaded {tf} model")
        else:
            print(f"  ✗ Model not found: {model_path}")
    except Exception as e:
        print(f"  ✗ Failed to load {tf} model: {e}")
    
    # โหลด Scaler (ถ้ามี)
    try:
        if os.path.exists(scaler_path):
            scalers[tf] = joblib.load(scaler_path)
            print(f"  ✓ Loaded {tf} scaler")
        else:
            print(f"  ⚠ Scaler not found: {scaler_path} (will use dynamic scaling)")
    except Exception as e:
        print(f"  ⚠ Failed to load {tf} scaler: {e}")

print("Models loaded!")


def predict_price(symbol: str = "BTCUSDT", timeframe: str = "1h"):
    """
    ทำนายราคาถัดไปสำหรับเหรียญและ timeframe ที่กำหนด
    ใช้ Multi-Feature Input และ Dynamic Scaling ต่อเหรียญ
    
    Args:
        symbol: สัญลักษณ์เหรียญ เช่น BTCUSDT, ETHUSDT
        timeframe: กรอบเวลา เช่น 5m, 1h, 4h
    
    Returns: 
        Tuple ของ (current_price, predicted_price)
    """
    # ดึงข้อมูลพร้อม features
    df, _ = get_training_data(symbol=symbol, interval=timeframe, limit=WINDOW + 100)
    data = df[FEATURE_COLUMNS].values
    
    # ถ้าไม่มีโมเดล ให้คืนค่าราคาปัจจุบัน
    if timeframe not in models:
        current = float(data[-1, 0])  # คอลัมน์แรกคือ close
        return current, current
    
    model = models[timeframe]
    
    # ใช้ Dynamic Scaling เพื่อให้ได้ผลลัพธ์ที่เหมาะกับเหรียญนั้นๆ
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled = scaler.fit_transform(data)
    
    # เตรียม input sequence
    X = scaled[-WINDOW:].reshape(1, WINDOW, len(FEATURE_COLUMNS))
    
    # ทำนาย
    pred_scaled = model.predict(X, verbose=0)
    
    # แปลงกลับเป็นราคาจริง
    # สร้าง dummy array เพื่อ inverse transform (ใส่ค่าทำนายที่คอลัมน์แรก)
    dummy = np.zeros((1, len(FEATURE_COLUMNS)))
    dummy[0, 0] = pred_scaled[0, 0]
    pred = scaler.inverse_transform(dummy)
    
    current_price = float(data[-1, 0])
    predicted_price = float(pred[0, 0])
    
    return current_price, predicted_price


def predict_with_history(symbol: str = "BTCUSDT", timeframe: str = "1h", history_limit: int = 50):
    """
    ทำนายราคาพร้อมคืนค่าข้อมูลย้อนหลังสำหรับแสดงกราฟ
    ใช้ Multi-Feature Input และ Dynamic Scaling
    
    Args:
        symbol: สัญลักษณ์เหรียญ
        timeframe: กรอบเวลา
        history_limit: จำนวนข้อมูลย้อนหลังที่ต้องการ
    
    Returns:
        Dict ที่มี times, actual_prices, predicted_prices, current, predicted
    """
    # ดึงข้อมูลพร้อม features
    df, _ = get_training_data(symbol=symbol, interval=timeframe, limit=history_limit + WINDOW + 50)
    data = df[FEATURE_COLUMNS].values
    times = df["time"].values
    
    # ถ้าไม่มีโมเดล ให้คืนค่าราคาจริงเท่านั้น
    if timeframe not in models:
        actual_prices = [float(p) for p in data[-history_limit:, 0]]
        time_labels = []
        for t in times[-history_limit:]:
            dt = datetime.fromtimestamp(t / 1000)
            time_labels.append(dt.strftime("%H:%M"))
        
        return {
            "times": time_labels,
            "actual_prices": actual_prices,
            "predicted_prices": actual_prices,
            "current": actual_prices[-1],
            "predicted": actual_prices[-1]
        }
    
    model = models[timeframe]
    
    # ใช้ Dynamic Scaling
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled = scaler.fit_transform(data)
    
    # สร้าง predictions สำหรับแต่ละจุดใน history
    actual_prices = []
    predicted_prices = []
    time_labels = []
    
    for i in range(WINDOW, len(scaled)):
        # สร้าง input sequence
        X = scaled[i-WINDOW:i].reshape(1, WINDOW, len(FEATURE_COLUMNS))
        
        # ทำนาย
        pred_scaled = model.predict(X, verbose=0)
        
        # แปลงกลับเป็นราคาจริง
        dummy = np.zeros((1, len(FEATURE_COLUMNS)))
        dummy[0, 0] = pred_scaled[0, 0]
        pred = scaler.inverse_transform(dummy)[0, 0]
        
        # เก็บค่า
        actual_prices.append(float(data[i, 0]))
        predicted_prices.append(float(pred))
        
        # แปลงเวลา
        dt = datetime.fromtimestamp(times[i] / 1000)
        time_labels.append(dt.strftime("%H:%M"))
    
    # ทำนายจุดถัดไป (อนาคต)
    current_price = float(data[-1, 0])
    X_final = scaled[-WINDOW:].reshape(1, WINDOW, len(FEATURE_COLUMNS))
    next_pred_scaled = model.predict(X_final, verbose=0)
    
    dummy = np.zeros((1, len(FEATURE_COLUMNS)))
    dummy[0, 0] = next_pred_scaled[0, 0]
    next_predicted = float(scaler.inverse_transform(dummy)[0, 0])
    
    # เพิ่มจุดทำนายอนาคต
    predicted_prices.append(next_predicted)
    actual_prices.append(current_price)
    
    # เพิ่ม label เวลาอนาคต
    last_time = datetime.fromtimestamp(times[-1] / 1000)
    if timeframe == "5m":
        future_minutes = 5
    elif timeframe == "1h":
        future_minutes = 60
    else:  # 4h
        future_minutes = 240
    
    future_time = last_time + timedelta(minutes=future_minutes)
    time_labels.append(future_time.strftime("%H:%M"))
    
    return {
        "times": time_labels,
        "actual_prices": actual_prices,
        "predicted_prices": predicted_prices,
        "current": current_price,
        "predicted": next_predicted
    }
