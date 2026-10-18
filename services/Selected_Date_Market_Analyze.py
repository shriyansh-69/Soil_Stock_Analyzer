import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import timedelta


# ---------------- FETCH DATA ----------------
def fetch_market_data_Two(ticker, start_date_obj, end_date_obj):

    fund = yf.Ticker(ticker)

    data = fund.history(
        start=start_date_obj,
        end=end_date_obj + timedelta(days=1)
    )

    adjusted = False

    if data.empty:
        return None, False, "Invalid ticker or no trading data available."

    data["Average_Price"] = data[["Open","High","Low","Close"]].mean(axis=1)

    return data, adjusted, None


# ---------------- ANALYSIS FUNCTION ----------------
def analyze_data(data, price_type, operation):

    all_columns = ["Open", "Close", "High", "Low", "Average_Price"]

    # Handle "All" price type
    if "All" in price_type:
        price_type = all_columns

    # Handle default operations
    if not operation or "All" in operation:
        operation = ["Lowest", "Highest", "Average"]

    results = {}

    for pt in price_type:
        if pt not in data.columns:
            continue

        results[pt] = {}

        if "Lowest" in operation:
            results[pt]["Lowest"] = data[pt].min()

        if "Highest" in operation:
            results[pt]["Highest"] = data[pt].max()

        if "Average" in operation:
            results[pt]["Average"] = data[pt].mean()

    df = pd.DataFrame(results).T

    return df.to_html(classes="analysis-table")


# ---------------- PLOT FUNCTION ----------------

def generate_plot_Two(data, price_type, ticker, start_date, end_date):

    fig = go.Figure()

    all_columns = ["Open","Close","High","Low","Average_Price"]

    if "All" in price_type:
        price_type = ["Open", "Close", "High", "Low", "Average_Price"]

    fig = go.Figure()

    for pt in price_type:
        if pt in data.columns:
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data[pt],
                    mode="lines",
                    name=pt
                )
            )

    fig.update_layout(
        title=f"{ticker} Price Chart ({start_date} to {end_date})",
        template="plotly_dark",
        height=600,
        xaxis_title="Date",
        yaxis_title="Price"
    )

    return fig.to_html(full_html=False)