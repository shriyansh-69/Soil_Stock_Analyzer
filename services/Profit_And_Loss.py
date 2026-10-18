import pandas as pd
import yfinance as yf
from datetime import timedelta
import plotly.graph_objects as go


def get_nearest_trading_day(data, date):
    if date in data.index:
        return date
    else:
        nearest = data.index[data.index <= date]
        if len(nearest) > 0:
            return nearest[-1]
        return None
    


def Profit_And_Loss_Analyzer(
    ticker,
    buy_date,
    sell_date,
    plot=False
):
    df = yf.download(
        ticker,
        start=pd.to_datetime(buy_date) - timedelta(days=5),
        end=pd.to_datetime(sell_date) + timedelta(days=5),
        progress=False
    )

    if df.empty:
        return {"error": "No data found for ticker."}

    # ✅ FIX: Flatten MultiLevel columns yfinance returns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.index = pd.to_datetime(df.index)

    buy_date  = pd.to_datetime(buy_date)
    sell_date = pd.to_datetime(sell_date)

    buy_actual  = get_nearest_trading_day(df, buy_date)
    sell_actual = get_nearest_trading_day(df, sell_date)

    if buy_actual is None or sell_actual is None:
        return {"error": "Invalid trading dates."}

    # ✅ FIX: Safe scalar extraction after flattening
    buy_price  = float(df.loc[buy_actual,  "Close"])
    sell_price = float(df.loc[sell_actual, "Close"])

    absolute_profit   = sell_price - buy_price
    percentage_change = (absolute_profit / buy_price) * 100
    status = "Profit" if absolute_profit > 0 else "Loss"

    plot_html = None

    if plot:
        padding = timedelta(days=3)

        df_plot = df.loc[
            buy_actual  - padding :
            sell_actual + padding
        ]

        # ✅ FIX: Ensure Close column is a clean 1D Series
        close_series = df_plot["Close"].squeeze()

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df_plot.index,
            y=close_series,          # ← was df_plot["Close"] which may be 2D
            mode="lines",
            name="Close Price",
            line=dict(color="#00cfff", width=2.5)
        ))

        fig.add_trace(go.Scatter(
            x=[buy_actual],
            y=[buy_price],
            mode="markers+text",
            marker=dict(size=14, color="#00ffaa", symbol="circle"),
            text=["Buy"],
            textposition="top center",
            name="Buy"
        ))

        fig.add_trace(go.Scatter(
            x=[sell_actual],
            y=[sell_price],
            mode="markers+text",
            marker=dict(size=14, color="#ff3f6c", symbol="circle"),
            text=["Sell"],
            textposition="top center",
            name="Sell"
        ))

        fig.update_layout(
            title=f"{ticker} Trade Analysis",
            template="plotly_dark",
            height=450,
            margin=dict(l=40, r=40, t=60, b=40),
            hovermode="x unified",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        plot_html = fig.to_html(full_html=False)

    return {
        "buy_price":               round(buy_price, 2),
        "sell_price":              round(sell_price, 2),
        "absolute_profit_per_share": round(absolute_profit, 2),
        "total_profit":            round(absolute_profit, 2),
        "roi":                     round(percentage_change, 2),
        "shares":                  1,
        "status":                  status,
        "buy_used":                buy_actual.date(),
        "sell_used":               sell_actual.date(),
        "plot_html":               plot_html
    }