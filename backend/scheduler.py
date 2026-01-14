"""
โมดูล Scheduler สำหรับระบบทำนายราคาคริปโต
ใช้ APScheduler ในการรันงานทำนายตามช่วงเวลาที่กำหนด
รองรับหลาย Timeframe (5m, 1h, 4h) และทำงานเป็น Background Service ร่วมกับ FastAPI
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
import logging
from datetime import datetime
from typing import Optional

# ตั้งค่า logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("scheduler")

# ตัวแปร Scheduler (singleton) - เก็บ instance เดียวเท่านั้น
_scheduler: Optional[AsyncIOScheduler] = None

# กำหนดเหรียญและ timeframes ที่รองรับ
COINS = {
    "BTC": "BTCUSDT",
    "ETH": "ETHUSDT"
}

TIMEFRAMES = {
    "5m": {
        "interval_minutes": 5,
        "description": "5 minutes"
    },
    "1h": {
        "interval_minutes": 60,
        "description": "1 hour"
    },
    "4h": {
        "interval_minutes": 240,
        "description": "4 hours"
    }
}


def job_listener(event):
    """
    ตัวรับฟังเหตุการณ์ของ scheduler
    บันทึกสถานะการทำงานและข้อผิดพลาดของงาน
    """
    if event.exception:
        logger.error(f"Job {event.job_id} failed with exception: {event.exception}")
    else:
        logger.info(f"Job {event.job_id} executed successfully")


def run_prediction_for_timeframe(timeframe: str):
    """
    รันการทำนายสำหรับทุกเหรียญใน timeframe ที่กำหนด
    นี่คืองานหลักที่จะถูกตั้งเวลารัน
    
    Args:
        timeframe: กรอบเวลาที่ต้องการทำนาย (5m, 1h, 4h)
    """
    # import ที่นี่เพื่อหลีกเลี่ยง circular imports
    from ai_engine import predict_price
    from db import save_prediction
    
    logger.info(f"▶ Starting prediction job for timeframe: {timeframe}")
    start_time = datetime.now()
    
    success_count = 0
    error_count = 0
    
    for coin, symbol in COINS.items():
        try:
            # ดึงผลทำนายจาก AI Engine
            current_price, predicted_price = predict_price(symbol, timeframe)
            
            # กำหนดทิศทางแนวโน้ม
            if predicted_price > current_price:
                trend = "Uptrend"
                change_pct = ((predicted_price - current_price) / current_price) * 100
            else:
                trend = "Downtrend"
                change_pct = ((current_price - predicted_price) / current_price) * 100
            
            # บันทึกผลทำนายลงฐานข้อมูล
            save_prediction(coin, timeframe, current_price, predicted_price, trend)
            
            logger.info(
                f"  ✓ {coin}/{timeframe}: Current=${current_price:,.2f}, "
                f"Predicted=${predicted_price:,.2f}, {trend} ({change_pct:.2f}%)"
            )
            success_count += 1
            
        except Exception as e:
            logger.error(f"  ✗ Failed to process {coin}/{timeframe}: {e}")
            error_count += 1
    
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(
        f"◼ Completed {timeframe} predictions: "
        f"{success_count} success, {error_count} errors, took {elapsed:.2f}s"
    )


def run_all_predictions():
    """
    รันการทำนายสำหรับทุกเหรียญและทุก timeframe
    นี่คืองานหลักที่รันทุก 1 ชั่วโมง
    """
    logger.info("=" * 60)
    logger.info("🚀 HOURLY PREDICTION JOB STARTED")
    logger.info(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    for timeframe in TIMEFRAMES.keys():
        run_prediction_for_timeframe(timeframe)
    
    logger.info("=" * 60)
    logger.info("✅ HOURLY PREDICTION JOB COMPLETED")
    logger.info("=" * 60 + "\n")


def get_scheduler() -> Optional[AsyncIOScheduler]:
    """ดึง instance ของ scheduler"""
    return _scheduler


def start_scheduler():
    """
    เริ่มการทำงาน background scheduler ร่วมกับ FastAPI
    ตั้งค่างานหลายรายการสำหรับ timeframe ต่างๆ
    """
    global _scheduler
    
    if _scheduler is not None:
        logger.warning("Scheduler already running!")
        return _scheduler
    
    # สร้าง AsyncIO scheduler (เข้ากันได้กับ async loop ของ FastAPI)
    _scheduler = AsyncIOScheduler(
        timezone="Asia/Bangkok",
        job_defaults={
            "coalesce": True,  # รวมการทำงานที่พลาดไป
            "max_instances": 1,  # ให้ทำงานได้ครั้งละ 1 instance เท่านั้น
            "misfire_grace_time": 300  # เวลาผ่อนผัน 5 นาที
        }
    )
    
    # เพิ่ม event listener สำหรับติดตามการทำงาน
    _scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    
    # ==========================================================
    # งานที่ 1: งานหลักประจำชั่วโมง - รันทุก 1 ชั่วโมง (ที่นาทีที่ 0)
    # รันการทำนายสำหรับทุก timeframe
    # ==========================================================
    _scheduler.add_job(
        run_all_predictions,
        trigger=CronTrigger(minute=0),  # รันที่จุดเริ่มต้นของทุกชั่วโมง
        id="hourly_all_predictions",
        name="Hourly All Predictions Job",
        replace_existing=True
    )
    logger.info("📅 Added job: Hourly All Predictions (every hour at minute 0)")
    
    # ==========================================================
    # งานที่ 2: การทำนาย 5 นาที
    # รันทุก 30 นาที สำหรับ timeframe 5m เท่านั้น
    # ==========================================================
    _scheduler.add_job(
        lambda: run_prediction_for_timeframe("5m"),
        trigger=IntervalTrigger(minutes=30),
        id="5m_predictions",
        name="5-Minute Predictions Job",
        replace_existing=True
    )
    logger.info("📅 Added job: 5-Minute Predictions (every 30 minutes)")
    
    # ==========================================================
    # งานที่ 3: การทำนาย 4 ชั่วโมง
    # รันทุก 4 ชั่วโมง สำหรับ timeframe 4h เท่านั้น
    # ==========================================================
    _scheduler.add_job(
        lambda: run_prediction_for_timeframe("4h"),
        trigger=CronTrigger(hour="*/4", minute=1),  # ทุก 4 ชั่วโมงที่นาทีที่ 1
        id="4h_predictions",
        name="4-Hour Predictions Job",
        replace_existing=True
    )
    logger.info("📅 Added job: 4-Hour Predictions (every 4 hours)")
    
    # เริ่มการทำงาน scheduler
    _scheduler.start()
    
    logger.info("=" * 60)
    logger.info("🎉 SCHEDULER STARTED SUCCESSFULLY")
    logger.info(f"   Active Jobs: {len(_scheduler.get_jobs())}")
    for job in _scheduler.get_jobs():
        logger.info(f"   • {job.name} (ID: {job.id})")
    logger.info("=" * 60)
    
    # รันการทำนายครั้งแรกเมื่อเริ่มต้น
    logger.info("Running initial predictions on startup...")
    try:
        run_all_predictions()
    except Exception as e:
        logger.error(f"Initial prediction failed: {e}")
    
    return _scheduler


def stop_scheduler():
    """
    หยุดการทำงาน scheduler อย่างสมบูรณ์
    เรียกใช้เมื่อปิด FastAPI
    """
    global _scheduler
    
    if _scheduler is not None:
        _scheduler.shutdown(wait=True)
        logger.info("Scheduler stopped successfully")
        _scheduler = None
    else:
        logger.warning("Scheduler was not running")


def get_scheduler_status():
    """
    ดึงสถานะปัจจุบันของ scheduler และข้อมูลงาน
    มีประโยชน์สำหรับการติดตามผ่าน API endpoint
    """
    if _scheduler is None:
        return {
            "running": False,
            "message": "Scheduler not started"
        }
    
    jobs = []
    for job in _scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": str(job.next_run_time) if job.next_run_time else None,
            "trigger": str(job.trigger)
        })
    
    return {
        "running": _scheduler.running,
        "timezone": str(_scheduler.timezone),
        "jobs": jobs,
        "job_count": len(jobs)
    }


# สำหรับการทดสอบ
if __name__ == "__main__":
    import asyncio
    
    async def main():
        start_scheduler()
        
        # รันต่อไปสำหรับการทดสอบ
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            stop_scheduler()
    
    asyncio.run(main())
