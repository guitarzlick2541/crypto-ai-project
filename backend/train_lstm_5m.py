"""
สคริปต์ Training LSTM สำหรับ timeframe 5 นาที
ใช้ Multi-Feature Input เพื่อเพิ่มความแม่นยำในการทำนาย
Features: close, open, high, low, volume, price_change, volatility, 
          ma_5, ma_10, ma_20, macd, rsi, bb_position, volume_change, price_position
"""

import os
import sys
# บังคับ encoding เป็น utf-8 เพื่อรองรับ path ภาษาไทย
sys.stdout.reconfigure(encoding='utf-8')

import numpy as np
import joblib
from data_service import get_training_data
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.optimizers import Adam

# ===== การตั้งค่า Configuration =====
TIMEFRAME = "5m"
WINDOW = 20  # จำนวนแท่งเทียนที่ใช้เป็น input
EPOCHS = 100
BATCH_SIZE = 32
VALIDATION_SPLIT = 0.2

# ใช้ absolute path จากตำแหน่งของไฟล์นี้
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "models")
MODEL_PATH = os.path.join(MODELS_DIR, f"lstm_{TIMEFRAME}.h5")
SCALER_PATH = os.path.join(MODELS_DIR, f"scaler_{TIMEFRAME}.pkl")

print(f"Training LSTM model for {TIMEFRAME} timeframe...")
print("=" * 50)

# ===== สร้างโฟลเดอร์ models ถ้ายังไม่มี =====
os.makedirs(MODELS_DIR, exist_ok=True)

# ===== ดึงข้อมูล Training Data =====
print("Fetching training data with multiple features...")
df, feature_columns = get_training_data(symbol="BTCUSDT", interval=TIMEFRAME, limit=1000)
data = df[feature_columns].values
print(f"Got {len(data)} samples with {len(feature_columns)} features")
print(f"Features: {feature_columns}")

# ===== Scale ข้อมูลทุก Features =====
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(data)

# ===== สร้าง Sequences =====
X, y = [], []
for i in range(WINDOW, len(scaled_data)):
    X.append(scaled_data[i-WINDOW:i])  # ใช้ทุก features
    y.append(scaled_data[i, 0])  # ทำนายราคาปิด (close price) ที่คอลัมน์แรก

X, y = np.array(X), np.array(y)
print(f"Created {len(X)} sequences with shape {X.shape}")

# ===== แบ่งข้อมูล Train/Validation =====
split_idx = int(len(X) * (1 - VALIDATION_SPLIT))
X_train, X_val = X[:split_idx], X[split_idx:]
y_train, y_val = y[:split_idx], y[split_idx:]
print(f"Training samples: {len(X_train)}, Validation samples: {len(X_val)}")

# ===== สร้างโมเดล =====
print("\nBuilding enhanced LSTM model...")
n_features = X.shape[2]

model = Sequential([
    # LSTM layer แรก
    LSTM(128, return_sequences=True, input_shape=(WINDOW, n_features)),
    BatchNormalization(),
    Dropout(0.2),
    
    # LSTM layer ที่สอง
    LSTM(64, return_sequences=True),
    BatchNormalization(),
    Dropout(0.2),
    
    # LSTM layer ที่สาม
    LSTM(32, return_sequences=False),
    BatchNormalization(),
    Dropout(0.2),
    
    # Dense layers
    Dense(32, activation='relu'),
    Dropout(0.1),
    Dense(16, activation='relu'),
    Dense(1)
])

# Compile โมเดล
optimizer = Adam(learning_rate=0.001)
model.compile(optimizer=optimizer, loss='mse', metrics=['mae'])

model.summary()

# ===== Callbacks =====
early_stop = EarlyStopping(
    monitor='val_loss',  # ติดตามค่า validation loss
    patience=15,         # หยุดถ้าไม่ดีขึ้นใน 15 epochs
    restore_best_weights=True,
    verbose=1
)

reduce_lr = ReduceLROnPlateau(
    monitor='val_loss',  # ลด learning rate เมื่อ validation loss ไม่ลดลง
    factor=0.5,
    patience=5,
    min_lr=0.00001,
    verbose=1
)

# ===== Train โมเดล =====
print("\nTraining model...")
history = model.fit(
    X_train, y_train,
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    validation_data=(X_val, y_val),
    callbacks=[early_stop, reduce_lr],
    verbose=1
)

# ===== ประเมินผล =====
print("\n" + "=" * 50)
train_loss, train_mae = model.evaluate(X_train, y_train, verbose=0)
val_loss, val_mae = model.evaluate(X_val, y_val, verbose=0)
print(f"Training   - Loss: {train_loss:.6f}, MAE: {train_mae:.6f}")
print(f"Validation - Loss: {val_loss:.6f}, MAE: {val_mae:.6f}")

# ===== บันทึกโมเดลและ Scaler =====
model.save(MODEL_PATH)
joblib.dump(scaler, SCALER_PATH)
print(f"\n[OK] Model saved to: {MODEL_PATH}")
print(f"[OK] Scaler saved to: {SCALER_PATH}")
print(f"[OK] Features: {n_features}")
print(f"[OK] Window size: {WINDOW}")
print("Training complete!")
