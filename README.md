# Crypto AI Prediction Dashboard

ระบบพยากรณ์ราคา Cryptocurrency อัจฉริยะด้วย AI (Deep Learning LSTM) ที่มาพร้อมกับหน้า Dashboard แสดงผลแบบเรียลไทม์ และระบบหลังบ้านที่แข็งแกร่ง

## ฟีเจอร์หลัก (Key Features)

*   **High-Performance LSTM Model:** ใช้โมเดล **LSTM (Long Short-Term Memory)** ที่เทรนด้วยข้อมูล **15+ Features** (RSI, MACD, Volume, MA, Volatility) เพื่อวิเคราะห์ความสัมพันธ์ของราคาที่ซับซ้อน
*   **Multi-Timeframe Analysis:** รองรับการทำนายครอบคลุมทุกระยะการเทรด:
    *   **5m:** สำหรับการสแกนระยะสั้นพิเศษ
    *   **1h:** สำหรับการวิเคราะห์แนวโน้มรายวัน
    *   **4h:** สำหรับการมองภาพรวมระยะกลาง
*   **Integrated Dashboard:**
    *   กราฟแบบ Hybrid แสดงราคาจริงเทียบกับราคาพยากรณ์ด้วย **Chart.js**
    *   **Trend Prediction:** แจ้งเตือนแนวโน้ม Uptrend/Downtrend พร้อมเปอร์เซ็นต์การเปลี่ยนแปลง
    *   **Real-time Simulation:** ระบบจำลองการอัปเดตราคาจาก Binance API
*   **UI-Driven Retraining:** สามารถสั่งเทรนโมเดลใหม่ (Refit) ได้โดยตรงจากหน้า Dashboard เพื่อให้ AI เรียนรู้พฤติกรรมตลาดล่าสุด
*   **Robust Scheduler:** ระบบงานเบื้องหลัง (APScheduler) ที่รันทำนายอัตโนมัติทุก 30 นาที และบันทึกผลลงฐานข้อมูล SQLite
*   **Comprehensive Testing:** ชุดทดสอบอัตโนมัติ (Pytest) ครอบคลุมทั้ง API, Data Loading, Feature Engineering และ Database Integrity

## เทคโนโลยีที่ใช้ (Tech Stack)

### Backend
*   **FastAPI:** รากฐานของระบบ API ที่รวดเร็วและรองรับการทำงานแบบ Asynchronous
*   **TensorFlow:** ขุมพลังหลักในการรันและจัดการโมเดล Deep Learning
*   **APScheduler:** จัดการการรัน AI ล่วงหน้าตามเวลาที่กำหนด
*   **SQLite:** จัดเก็บประวัติการทำนายและสถิติโมเดล
*   **Scikit-learn:** จัดการการย่อส่วนข้อมูล (Scaling) และประเมินผล

### Frontend
*   **Glassmorphism Design:** ใช้ CSS ขั้นสูงสร้าง UI ที่ดูโปร่งใส ทันสมัย และสะอาดตา
*   **Vanilla JS:** ปราศจาก Framework หนักๆ ทำให้โหลดเร็วและโต้ตอบได้ทันใจ
*   **CSS One-File:** รวมสไตล์ทั้งหมดไว้ในไฟล์เดียวเพื่อให้ง่ายต่อการจัดการ

## การติดตั้งและการใช้งาน

1.  **ติดตั้ง Dependencies:**
    ```bash
    pip install -r backend/requirements.txt
    ```

2.  **เริ่มโปรแกรม:**
    ```bash
    python run.py
    ```
    *ระบบจะทำการ Initialize ฐานข้อมูลและเริ่มรัน Server ที่ `http://localhost:8000`*

## โครงสร้างโปรเจค (Project Structure)

```
crypto-ai-project/
├── backend/
│   ├── tests/              # ชุดทดสอบ (test_main.py, test_core.py)
│   ├── ai_engine.py        # สมอง AI: โหลดโมเดลและทำนายผล
│   ├── main.py             # FastAPI: จุดเชื่อมต่อ API ทั้งหมด
│   ├── scheduler.py        # งานอัตโนมัติ: บันทึกข้อมูลลง DB รายชั่วโมง
│   ├── data_service.py     # ดึงข้อมูลราคาและคำนวณ Technical Indicators
│   ├── db.py               # จัดการฐานข้อมูล SQLite
│   ├── backtest.py         # ระบบจำลองการพยากรณ์ย้อนหลัง
│   └── train_model.py      # สคริปต์เทรน AI (รองรับทุก Timeframe)
├── frontend/
│   ├── index.html          # โครงสร้างหน้า Dashboard
│   ├── style.css           # ดีไซน์ทั้งหมด (Mobile Responsive)
│   └── script.js           # Logic การสั่งงานหน้าเว็บบอร์ด
├── models/                 # ที่เก็บไฟล์โมเดล AI (.h5) และ Scalers (.pkl)
├── run.py                  # ตัวรันโปรแกรมหลัก (API Server)
└── run_tests_custom.py     # ตัวรันชุดทดสอบ (Test Runner)
```

## การตรวจสอบคุณภาพ (Quality Assurance)
เราให้ความสำคัญกับความถูกต้องของข้อมูล คุณสามารถรันชุดทดสอบทั้งหมดได้ด้วยคำสั่งเดียว:
```bash
python run_tests_custom.py
```
*ระบบจะแสดงผลลัพธ์การทดสอบแต่ละหัวข้ออย่างละเอียด*

---
© 2026 Crypto AI Prediction System | *Built for Precision & Performance*
