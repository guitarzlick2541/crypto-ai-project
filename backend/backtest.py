import numpy as np
from data_service import get_klines

def backtest(symbol: str = "BTCUSDT", timeframe: str = "1h"):
    """
    รันการทดสอบย้อนหลัง (Backtest) แบบง่าย โดยใช้ Naive Prediction (ใช้ราคาก่อนหน้า)
    เพื่อใช้เป็นค่าพื้นฐาน (Baseline) เปรียบเทียบกับ AI Model
    
    Args:
        symbol: คู่เหรียญ (เช่น BTCUSDT, ETHUSDT)
        timeframe: ช่วงเวลา (5m, 1h, 4h)
    
    Returns:
        Tuple ของ (mae, rmse)
        - MAE: Mean Absolute Error (ความคลาดเคลื่อนเฉลี่ย)
        - RMSE: Root Mean Squared Error (รากที่สองของความคลาดเคลื่อนกำลังสองเฉลี่ย)
    """
    # ดึงข้อมูลราคาย้อนหลัง
    df = get_klines(symbol=symbol, interval=timeframe)
    prices = df["close"].values
    
    # การทำนายแบบ Naive: ใช้ราคาปิดของระยเวลาก่อนหน้า เป็นค่าทำนายของปัจจุบัน
    # (สมมติว่าราคาจะไม่เปลี่ยนแปลง)
    y_true = prices[1:]      # ราคาจริง (ตั้งเแต่ช่วงที่ 2 เป็นต้นไป)
    y_pred = prices[:-1]     # ราคาทำนาย (เอาช่วงที่ 1 มาทายช่วงที่ 2)
    
    # คำนวณค่าชี้วัดความแม่นยำ (Metrics)
    mae = np.mean(np.abs(y_true - y_pred))
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
    
    return float(mae), float(rmse)
