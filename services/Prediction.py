import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential 
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
from tensorflow.keras.callbacks import EarlyStopping
import plotly.graph_objects as go


# =========================================
# Get Historical Data
# =========================================

def get_fund_data(ticker, period="5y"):

    df = yf.download(ticker, period=period, progress=False)

    if df.empty:
        return None

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.ffill().bfill()

    return df[["Open", "High", "Low", "Close", "Volume"]]


# =========================================
# Prediction Model
# =========================================

def predict_future_prices(df, sequence_length=60, n_future=30):

    df_close = df[['Close']].copy().ffill().bfill()

    if len(df_close) < sequence_length + n_future:
        return None

    scaler = MinMaxScaler()
    df_scaled = scaler.fit_transform(df_close)

    X, Y = [], []

    for i in range(len(df_scaled) - sequence_length - n_future + 1):
        X.append(df_scaled[i:i+sequence_length])
        Y.append(df_scaled[i+sequence_length:i+sequence_length+n_future])

    X = np.array(X)
    Y = np.array(Y)

    split = int(len(X) * 0.8)

    X_train, Y_train = X[:split], Y[:split]
    X_test, Y_test = X[split:], Y[split:]

    model = Sequential([
        Input(shape=(sequence_length, 1)),
        LSTM(64),
        Dropout(0.3),
        Dense(n_future)
    ])

    model.compile(optimizer="adam", loss="mse")

    early_stop = EarlyStopping(
        patience=10,
        restore_best_weights=True
    )

    model.fit(
        X_train,
        Y_train,
        validation_data=(X_test, Y_test),
        epochs=60,
        batch_size=16,
        callbacks=[early_stop],
        verbose=1
    )

    last_sequence = df_scaled[-sequence_length:].reshape(1, sequence_length, 1)

    future_scaled = model.predict(last_sequence)[0]

    future_prices = scaler.inverse_transform(
        future_scaled.reshape(-1, 1)
    ).flatten()

    future_dates = pd.date_range(
        df.index[-1] + pd.Timedelta(days=1),
        periods=n_future
    )

    future_df = pd.DataFrame({
        "Date": future_dates,
        "Predicted_Close": future_prices
    })

    return future_df


# =========================================
# Generate BUY / SELL / HOLD Signal
# =========================================

def generate_signal(current_price, future_price, buy=0.02, sell=-0.02):

    change = (future_price - current_price) / current_price

    if change > buy:
        return f"BUY 📈 (+{change*100:.2f}%)"

    elif change < sell:
        return f"SELL 📉 ({change*100:.2f}%)"

    else:
        return f"HOLD 🤝 ({change*100:.2f}%)"


# =========================================
# Plot Chart for HTML
# =========================================

def plot_prediction(future_df):
    fig = go.Figure()

    # Only predicted future prices
    fig.add_trace(go.Scatter(
        x=future_df["Date"],
        y=future_df["Predicted_Close"],
        mode="lines+markers",
        name="Predicted"
    ))

    fig.update_layout(
        template="plotly_dark",
        title="Predicted Close Price (Next 30 Days)",
        xaxis_title="Date",
        yaxis_title="Price",
        height=450,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    return fig.to_html(full_html=False)