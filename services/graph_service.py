import pandas as pd
import yfinance as yf
import plotly.graph_objects as go


def Graph_Plotter(
    ticker: str,
    start_date: str = None,
    end_date: str = None,
    price_type: str = "Close",
    moving_averages: str = None,
    plot: bool = True
):
    """
    Pure business logic graph plotter.
    Returns structured dictionary with optional plot HTML.
    """

    try:
        df = yf.download(
            ticker,
            start=start_date,
            end=end_date,
            progress=False
        )

        if df.empty:
            return {"error": "No data found for ticker."}

        # ✅ Flatten MultiIndex (yfinance fix)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df.index = pd.to_datetime(df.index)

        # ✅ Validate price column
        if price_type not in df.columns:
            return {"error": f"Invalid price type '{price_type}'."}

        selected_series = df[price_type].squeeze()

        plot_html = None

        # ==============================
        # 📊 Plot Section (Optional)
        # ==============================
        if plot:
            fig = go.Figure()

            # Main Price Line
            fig.add_trace(go.Scatter(
                x=df.index,
                y=selected_series,
                mode="lines",
                name=price_type,
                line=dict(width=2.5)
            ))

            # ==============================
            # 📈 Moving Averages
            # ==============================
            valid_windows = []

            if moving_averages:
                for value in moving_averages.split(","):
                    try:
                        window = int(value.strip())
                        if window > 0:
                            valid_windows.append(window)
                    except ValueError:
                        continue

            for window in valid_windows:
                if window < len(df):
                    ma_series = selected_series.rolling(window=window).mean()

                    fig.add_trace(go.Scatter(
                        x=df.index,
                        y=ma_series,
                        mode="lines",
                        name=f"{window}-Day MA"
                    ))

            fig.update_layout(
                title=f"{ticker} {price_type} Chart",
                template="plotly_dark",
                height=500,
                margin=dict(l=40, r=40, t=60, b=40),
                hovermode="x unified",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )

            plot_html = fig.to_html(full_html=False)

        # ==============================
        # 📦 Return Structured Output
        # ==============================
        return {
            "ticker": ticker.upper(),
            "price_type": price_type,
            "start_date": start_date,
            "end_date": end_date,
            "available_columns": list(df.columns),
            "moving_averages_used": valid_windows,
            "total_rows": len(df),
            "plot_html": plot_html
        }

    except Exception as e:
        return {"error": str(e)}