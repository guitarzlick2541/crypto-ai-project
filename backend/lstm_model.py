import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler

scaler = MinMaxScaler()
model = None
WINDOW = 24  # 24 ชั่วโมงย้อนหลัง

def train_lstm(prices):
    global model

    prices = np.array(prices).reshape(-1, 1)
    scaled = scaler.fit_transform(prices)

    X, y = [], []
    for i in range(WINDOW, len(scaled)):
        X.append(scaled[i-WINDOW:i])
        y.append(scaled[i])

    X, y = np.array(X), np.array(y)

    model = Sequential([
        LSTM(50, return_sequences=True, input_shape=(WINDOW, 1)),
        LSTM(50),
        Dense(1)
    ])

    model.compile(optimizer="adam", loss="mse")
    model.fit(X, y, epochs=5, batch_size=16, verbose=0)

def predict_next_price(prices):
    global model

    if model is None:
        train_lstm(prices)

    prices = np.array(prices).reshape(-1, 1)
    scaled = scaler.transform(prices)

    last_window = scaled[-WINDOW:]
    last_window = last_window.reshape(1, WINDOW, 1)

    pred_scaled = model.predict(last_window, verbose=0)
    pred_price = scaler.inverse_transform(pred_scaled)

    return float(pred_price[0][0])
