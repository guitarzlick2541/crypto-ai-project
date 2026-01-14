import numpy as np
from data_service import get_klines

def backtest(symbol: str = "BTCUSDT", timeframe: str = "1h"):
    """
    Run a simple backtest using naive prediction (previous price).
    
    Args:
        symbol: Trading pair symbol (e.g., BTCUSDT, ETHUSDT)
        timeframe: Time interval (5m, 1h, 4h)
    
    Returns:
        Tuple of (mae, rmse)
    """
    # Get historical data
    df = get_klines(symbol=symbol, interval=timeframe)
    prices = df["close"].values
    
    # Naive prediction: use previous price as prediction
    y_true = prices[1:]
    y_pred = prices[:-1]
    
    # Calculate metrics
    mae = np.mean(np.abs(y_true - y_pred))
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
    
    return float(mae), float(rmse)
