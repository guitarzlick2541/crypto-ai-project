import requests
import pandas as pd
import numpy as np
from datetime import datetime

def get_klines(symbol="BTCUSDT", interval="1h", limit=300):
    """ดึงข้อมูลแท่งเทียนพื้นฐานสำหรับการทำนาย"""
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    data = requests.get(url, params=params).json()

    df = pd.DataFrame(data, columns=[
        "time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades", "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
    
    return df[["time", "close"]]


def get_ohlcv_data(symbol="BTCUSDT", interval="1h", limit=50):
    """ดึงข้อมูล OHLCV สำหรับตารางประวัติ"""
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    data = requests.get(url, params=params).json()
    
    result = []
    for row in data:
        timestamp = int(row[0])
        dt = datetime.fromtimestamp(timestamp / 1000)
        
        result.append({
            "date": dt.strftime("%Y-%m-%d"),
            "time": dt.strftime("%H:%M:%S"),
            "open": float(row[1]),
            "high": float(row[2]),
            "low": float(row[3]),
            "close": float(row[4]),
            "volume": float(row[5]),
            "change": round((float(row[4]) - float(row[1])) / float(row[1]) * 100, 2)
        })
    
    # ส่งคืนข้อมูลเรียงจากใหม่สุดไปเก่าสุด
    return list(reversed(result))


def get_training_data(symbol="BTCUSDT", interval="1h", limit=1000):
    """ดึงข้อมูลสำหรับเทรนโมเดลแบบ Multi-Feature"""
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    data = requests.get(url, params=params).json()

    df = pd.DataFrame(data, columns=[
        "time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades", "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
    
    # สร้าง Features เพิ่มเติม (Feature Engineering)
    df["price_change"] = df["close"].pct_change() * 100
    df["volatility"] = (df["high"] - df["low"]) / df["close"] * 100
    df["ma_5"] = df["close"].rolling(window=5).mean()
    df["ma_10"] = df["close"].rolling(window=10).mean()
    df["ma_20"] = df["close"].rolling(window=20).mean()
    df["ema_12"] = df["close"].ewm(span=12, adjust=False).mean()
    df["ema_26"] = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"] = df["ema_12"] - df["ema_26"]
    
    # คำนวณ RSI
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df["rsi"] = 100 - (100 / (1 + rs))
    
    # คำนวณ Bollinger Bands
    df["bb_middle"] = df["close"].rolling(window=20).mean()
    bb_std = df["close"].rolling(window=20).std()
    df["bb_upper"] = df["bb_middle"] + (bb_std * 2)
    df["bb_lower"] = df["bb_middle"] - (bb_std * 2)
    df["bb_position"] = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])
    
    df["volume_change"] = df["volume"].pct_change() * 100
    df["price_position"] = (df["close"] - df["low"]) / (df["high"] - df["low"])
    
    df = df.dropna()
    
    feature_columns = [
        "close", "open", "high", "low", "volume",
        "price_change", "volatility",
        "ma_5", "ma_10", "ma_20",
        "macd", "rsi", "bb_position",
        "volume_change", "price_position"
    ]
    
    return df[["time"] + feature_columns], feature_columns
