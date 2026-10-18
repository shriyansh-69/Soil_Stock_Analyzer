import yfinance as yf
import pandas as pd
import plotly.graph_objects as go


# ---------------- FETCH DATA ----------------
def fetch_market_data(ticker, n_day=None):

    fund = yf.Ticker(ticker)
    data = fund.history(period="max")

    if data.empty:
        return None, "Invalid ticker or no data available."

    data["Average_Price"] = data[["Open","High","Low","Close"]].mean(axis=1)

    if n_day is not None:
        data = data.tail(n_day)

    return data, None


# ---------------- ANALYSIS FUNCTION ----------------
def analyze_data(data, price_type, operation):

    all_columns = ["Open","Close","High","Low","Average_Price"]

    if "All" in price_type:
        price_type = all_columns

    results = {}

    for pt in price_type:
        if pt not in data.columns:
            continue

        results[pt] = {}

        if not operation or "All" in operation:
            operation = ["Lowest","Highest","Average"]

        if "Lowest" in operation:
            results[pt]["Lowest"] = data[pt].min()

        if "Highest" in operation:
            results[pt]["Highest"] = data[pt].max()

        if "Average" in operation:
            results[pt]["Average"] = data[pt].mean()

    df = pd.DataFrame(results).T
    return df.to_html(classes="analysis-table")


# ---------------- PLOT FUNCTION ----------------
def generate_plot(data, price_type, ticker):

    fig = go.Figure()

    price_type =  ["Open", "Close", "High", "Low", "Average_Price"]

    price_type = list(set(price_type))

    if "All" in price_type:
        price_type = ["Open", "Close", "High", "Low", "Average_Price"]

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
        title=f"{ticker} Price Chart",
        template="plotly_dark",
        height=600,
        xaxis_title="Date",
        yaxis_title="Price"
    )

    return fig.to_html(full_html=False)