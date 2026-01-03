from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from binance_service import get_prices
from lstm_model import predict_next_price
from database import init_db, save_prediction, get_history

app = FastAPI(title="Crypto AI Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

@app.get("/")
def root():
    return {"status": "API running"}

@app.get("/predict")
def predict(symbol: str = "BTCUSDT"):
    prices = get_prices(symbol)
    actual = prices[-1]
    predicted = predict_next_price(prices)

    save_prediction(symbol, actual, predicted)

    return {
        "symbol": symbol,
        "actual_price": round(actual, 2),
        "predicted_price": round(predicted, 2),
        "trend": "Bullish" if predicted > actual else "Bearish"
    }

@app.get("/history")
def history():
    return get_history()
