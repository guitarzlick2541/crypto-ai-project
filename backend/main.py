from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ai_engine import predict_price, predict_with_history, models, scalers, MODELS_DIR, load_specific_model
from backtest import backtest
from data_service import get_klines, get_ohlcv_data
from scheduler import start_scheduler, stop_scheduler, get_scheduler_status
from db import init_db
from datetime import datetime
import subprocess
import sys
import os
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ทำงานเมื่อเริ่มต้น Server (Startup)
    init_db()
    start_scheduler()
    yield
    # ทำงานเมื่อปิด Server (Shutdown)
    stop_scheduler()

app = FastAPI(title="CryptoAI API", version="1.0.0", lifespan=lifespan)

# ... (Existing code) ...

@app.post("/retrain")
def retrain_model(timeframe: str = "1h"):
    """สั่งเทรนโมเดลใหม่ตาม Timeframe ที่ระบุ"""
    if timeframe not in ["5m", "1h", "4h"]:
        return {"status": "error", "message": "Invalid timeframe"}

    current_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(current_dir, "train_model.py")
    
    try:
        # รันสคริปต์เทรนแบบ Generic โดยส่ง Parameter ไป
        result = subprocess.run(
            [sys.executable, script_path, "--timeframe", timeframe], 
            capture_output=True, 
            text=True,
            encoding='utf-8',  # บังคับอ่าน output เป็น utf-8
            check=True
        )
        
        # Reload โมเดลใหม่ทันที
        load_specific_model(timeframe)
        
        return {
            "status": "success", 
            "message": f"Model {timeframe} retrained and reloaded successfully",
            "logs": result.stdout[-200:] # ส่ง Log พารากราฟสุดท้ายกลับไปให้ดู
        }
    except subprocess.CalledProcessError as e:
        return {
            "status": "error", 
            "message": f"Training failed: {e.stderr}"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# เหรียญที่รองรับ
SUPPORTED_COINS = {
    "BTC": "BTCUSDT",
    "ETH": "ETHUSDT"
}

@app.get("/")
def home():
    return {
        "status": "CryptoAI API Running",
        "supported_coins": list(SUPPORTED_COINS.keys()),
        "endpoints": ["/predict", "/backtest", "/coins", "/history", "/ohlcv", "/performance", "/debug/models"]
    }

@app.get("/debug/models")
def debug_models():
    """ตรวจสอบสถานะการโหลดโมเดล AI"""
    return {
        "models_directory": MODELS_DIR,
        "directory_exists": os.path.exists(MODELS_DIR),
        "loaded_models": list(models.keys()),
        "loaded_scalers": list(scalers.keys()),
        "models_count": len(models),
        "scalers_count": len(scalers),
        "status": "OK" if len(models) == 3 else "MODELS_NOT_LOADED"
    }

@app.get("/coins")
def get_coins():
    """ดึงรายชื่อเหรียญที่รองรับ"""
    return {"coins": list(SUPPORTED_COINS.keys())}

@app.get("/timeframes")
def get_timeframes():
    """ดึง Timeframes ที่รองรับ"""
    return {"timeframes": ["5m", "1h", "4h"]}

@app.get("/history")
def get_history(coin: str = "BTC", timeframe: str = "1h", limit: int = 50):
    """ดึงข้อมูลราคาย้อนหลังสำหรับแสดงกราฟ"""
    if coin.upper() not in SUPPORTED_COINS:
        return {"error": f"Coin {coin} not supported"}
    
    symbol = SUPPORTED_COINS[coin.upper()]
    df = get_klines(symbol=symbol, interval=timeframe, limit=limit)
    
    prices = df["close"].tolist()
    times = df["time"].tolist()
    
    formatted_times = []
    for t in times:
        dt = datetime.fromtimestamp(t / 1000)
        formatted_times.append(dt.strftime("%H:%M"))
    
    return {
        "coin": coin.upper(),
        "symbol": symbol,
        "timeframe": timeframe,
        "times": formatted_times,
        "prices": prices
    }

@app.get("/ohlcv")
def get_ohlcv(coin: str = "BTC", timeframe: str = "1h", limit: int = 50):
    """ดึงข้อมูล OHLCV สำหรับตารางประวัติ"""
    if coin.upper() not in SUPPORTED_COINS:
        return {"error": f"Coin {coin} not supported"}
    
    symbol = SUPPORTED_COINS[coin.upper()]
    data = get_ohlcv_data(symbol=symbol, interval=timeframe, limit=limit)
    
    return {
        "coin": coin.upper(),
        "symbol": symbol,
        "timeframe": timeframe,
        "data": data
    }

@app.get("/predict")
def predict(coin: str = "BTC", timeframe: str = "1h"):
    """ดึงผลการทำนายราคาพร้อมข้อมูลประวัติสำหรับกราฟ"""
    if coin.upper() not in SUPPORTED_COINS:
        return {"error": f"Coin {coin} not supported"}
    
    symbol = SUPPORTED_COINS[coin.upper()]
    result = predict_with_history(symbol, timeframe)
    
    return {
        "coin": coin.upper(),
        "symbol": symbol,
        "timeframe": timeframe,
        **result
    }

@app.get("/backtest")
def run_backtest(coin: str = "BTC", timeframe: str = "1h"):
    """รัน Backtest สำหรับเหรียญที่เลือก"""
    if coin.upper() not in SUPPORTED_COINS:
        return {"error": f"Coin {coin} not supported"}
    
    symbol = SUPPORTED_COINS[coin.upper()]
    mae, rmse = backtest(symbol, timeframe)
    
    return {
        "coin": coin.upper(),
        "symbol": symbol,
        "timeframe": timeframe,
        "mae": mae,
        "rmse": rmse
    }

@app.get("/performance")
def get_performance(coin: str = "BTC"):
    """ดึงประสิทธิภาพของโมเดลสำหรับทุก Timeframe"""
    if coin.upper() not in SUPPORTED_COINS:
        return {"error": f"Coin {coin} not supported"}
    
    symbol = SUPPORTED_COINS[coin.upper()]
    
    results = {}
    for tf in ["5m", "1h", "4h"]:
        try:
            mae, rmse = backtest(symbol, tf)
            # คำนวณความแม่นยำ (ส่วนกลับของ error)
            current, predicted = predict_price(symbol, tf)
            error_pct = abs(predicted - current) / current * 100
            accuracy = max(0, 100 - error_pct)
            
            results[tf] = {
                "mae": mae,
                "rmse": rmse,
                "accuracy": accuracy,
                "current_price": current,
                "predicted_price": predicted
            }
        except Exception as e:
            results[tf] = {"error": str(e)}
    
    return {
        "coin": coin.upper(),
        "symbol": symbol,
        "performance": results
    }

@app.get("/scheduler")
def scheduler_status():
    """ดึงสถานะ Scheduler และข้อมูลงาน"""
    return get_scheduler_status()
