import requests
import pandas as pd

URL = "https://api.binance.com/api/v3/klines"

def get_prices(symbol="BTCUSDT", interval="1h", limit=200):
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    r = requests.get(URL, params=params)
    data = r.json()

    df = pd.DataFrame(data, columns=[
        "open_time","open","high","low","close",
        "volume","close_time","qav","trades",
        "tb","tq","ignore"
    ])

    df["close"] = df["close"].astype(float)
    return df["close"].values
