# =====================================================
# 🔹 IMPORTS
# =====================================================

## --------------- FastAPI -------------------
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

## --------------- Other Libraries -------------------
import pandas as pd
import yfinance as yf
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, date
from groq import Groq

# =====================================================
# 🔹 Loading The API Key 
# =====================================================
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("⚠ GROQ_API_KEY not found in environment variables.")
else:
    client = Groq(api_key=GROQ_API_KEY)

#--------------------------------- Function's -----------------------------
from services.analysis_recent import (
    fetch_market_data,
    analyze_data,
    generate_plot
)

from services.Selected_Date_Market_Analyze import (
    fetch_market_data_Two,
    analyze_data,
    generate_plot_Two
) 

from services.Profit_And_Loss import Profit_And_Loss_Analyzer

from services.graph_service import Graph_Plotter

from services.Prediction import get_fund_data,generate_signal,predict_future_prices,plot_prediction

from services.chatbot import chatbot

class ChatRequest(BaseModel):
    message: str


# =====================================================
# 🔹 APP SETUP
# =====================================================
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
                            



@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("chatbot.html", {"request": request})



@app.post("/chat")
def chat_endpoint(request: ChatRequest):

    response = chatbot(request.message)

    return {
        "user_message": request.message,
        "bot_response": response
    }








# =====================================================
# 🔹 Price Checker  FUNCTIONS
# =====================================================
def get_price_for_date(ticker: str, selected_date: str):
    try:
        stock = yf.Ticker(ticker)
        date_obj = datetime.strptime(selected_date, "%Y-%m-%d")

        # Weekend check
        if date_obj.weekday() >= 5:
            return None, "Market Closed (Weekend)"

        next_day = date_obj + timedelta(days=1)

        data = stock.history(
            start=selected_date,
            end=next_day.strftime("%Y-%m-%d")
        )

        if not data.empty:
            result = {
                "ticker": ticker,
                "price": round(float(data["Close"].iloc[0]), 2),
                "currency": stock.info.get("currency", "Unknown"),
                "label": selected_date
            }
            return result, None

        return None, "No market data available"

    except:
        return None, "Invalid request"
    

###----------------------------------------------------- Get -------------------------------------------------------------
@app.get("/price_checker", response_class=HTMLResponse)
async def price_page(request: Request):
    today = date.today().strftime("%Y-%m-%d")

    return templates.TemplateResponse(
        "price_checker.html",
        {
            "request": request,
            "result": None,
            "error": None,
            "ticker": None,
            "today": today,
            "selected_date": today   # 👈 THIS IS REQUIRED
        }
    )

###----------------------------------------------------- Post -------------------------------------------------------------

@app.post("/price_checker", response_class=HTMLResponse)
async def price_checker(
    request: Request,
    ticker: str = Form(...),
    selected_date: str = Form(None)
):

    ticker = ticker.upper().strip()
    today = date.today().strftime("%Y-%m-%d")

    if not selected_date:
        selected_date = today

    result, error = get_price_for_date(ticker, selected_date)

    return templates.TemplateResponse(
        "price_checker.html",
        {
            "request": request,
            "result": result,
            "error": error,
            "ticker": ticker,
            "today": today,
            "selected_date": selected_date
        }
    )




# ==============================
# 🔹 3) Recent Market Analyzer
# ==============================

# -----------------------------------------------------------------------  Get Endpoint------------------------------------------
@app.get("/RecentTrendAnalysis", response_class=HTMLResponse)
async def analyzer_page(request: Request):
    return templates.TemplateResponse(
        "recent_market.html",
        {"request": request}
    )
# -------------------------------------------------
# POST ENDPOINT
# -------------------------------------------------
@app.post("/RecentTrendAnalysis", response_class=HTMLResponse)
async def recent_trend_analysis(
    request: Request,
    ticker: str = Form(...),
    price_type: list[str] = Form(...),
    n_day_input: str = Form(...),
    operation: list[str] = Form(None),
    action: str = Form(...)
):

    ticker = ticker.upper().strip()

    # -------- Convert Days --------
    if n_day_input.lower() == "all":
        n_day = None
    else:
        try:
            n_day = int(n_day_input)
        except ValueError:
            return templates.TemplateResponse(
                "recent_market.html",
                {
                    "request": request,
                    "error": "Invalid number of days",
                    "ticker": ticker
                }
            )

    # -------- Validate Price Type --------
    if not price_type:
        return templates.TemplateResponse(
            "recent_market.html",
            {
                "request": request,
                "error": "Select at least one Price Type",
                "ticker": ticker
            }
        )

    price_type = list(set(price_type))  # remove duplicates

    # -------- Fetch Data (Service Layer) --------
    data, error = fetch_market_data(ticker, n_day)

    if error:
        return templates.TemplateResponse(
            "recent_market.html",
            {
                "request": request,
                "error": error,
                "ticker": ticker
            }
        )

    result_html = None
    plot_html = None

    # -------- ANALYZE --------
    if action == "analyze":
        result_html = analyze_data(data, price_type, operation)

    # -------- PLOT --------
    if action == "plot":
        plot_html = generate_plot(data, price_type, ticker)

    return templates.TemplateResponse(
        "recent_market.html",
        {
            "request": request,
            "result_html": result_html,
            "plot_html": plot_html,
            "ticker": ticker,
            "price_type": price_type,
            "n_day_input": n_day_input,
            "operation": operation,
            "error": None
        }
    )




# ==============================
# 🔹 4) Custom Date Analysis 
# ==============================

@app.get("/Custom_Date_Analysis", response_class=HTMLResponse)
async def prediction_page(request: Request):

    today = datetime.today().date()

    return templates.TemplateResponse(
        "Custom_Date_Analysis.html",
        {
            "request": request,
            "today": today.isoformat()
        }
    )



@app.post("/Custom_Date_Analysis", response_class=HTMLResponse)
async def custom_date_analysis(
    request: Request,
    ticker: str = Form(...),
    price_type: list[str] = Form(None),
    start_date: str = Form(...),
    end_date: str = Form(...),
    operation: list[str] = Form(None),
    action: str = Form(...)
):

    # -------- Normalize Ticker --------
    ticker = ticker.upper().strip()

    today = datetime.today().date()

    # -------- Validate Dates --------
    try:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()

        if start_date_obj > end_date_obj:
            raise ValueError("Start date cannot be after End date")

        if start_date_obj > today or end_date_obj > today:
            raise ValueError("Future dates are not allowed")

    except ValueError as e:
        return templates.TemplateResponse(
            "Custom_Date_Analysis.html",
            {
                "request": request,
                "error": str(e),
                "ticker": ticker,
                "start_date": start_date,
                "end_date": end_date,
                "price_type": price_type,
                "operation": operation,
                "today": today.isoformat()
            }
        )

    # -------- Validate Price Type --------
    if not price_type:
        return templates.TemplateResponse(
            "Custom_Date_Analysis.html",
            {
                "request": request,
                "error": "Select at least one Price Type",
                "ticker": ticker,
                "start_date": start_date,
                "end_date": end_date,
                "operation": operation,
                "today": today.isoformat()
            }
        )

    price_type = list(set(price_type))

    # -------- Default Operation --------
    if not operation:
        operation = ["Lowest", "Highest", "Average"]

    # -------- Fetch Data --------
    data, adjusted, error = fetch_market_data_Two(
        ticker,
        start_date_obj,
        end_date_obj
    )

    if error:
        return templates.TemplateResponse(
            "Custom_Date_Analysis.html",
            {
                "request": request,
                "error": error,
                "ticker": ticker,
                "price_type": price_type,
                "start_date": start_date,
                "end_date": end_date,
                "operation": operation,
                "today": today.isoformat()
            }
        )

    result_html = None
    plot_html = None
    adjustment_message = None

    # -------- Date Adjustment Message --------
    if adjusted:
        adjustment_message = "Selected date included non-trading days. Adjusted to nearest valid trading dates."

    # -------- ANALYZE --------
    if action == "analyze":
        result_html = analyze_data(data, price_type, operation)

    # -------- PLOT --------
    elif action == "plot":
        plot_html = generate_plot_Two(
            data,
            price_type,
            ticker,
            start_date,
            end_date
        )

    # -------- Render Template --------
    return templates.TemplateResponse(
        "Custom_Date_Analysis.html",
        {
            "request": request,
            "result_html": result_html,
            "plot_html": plot_html,
            "ticker": ticker,
            "price_type": price_type,
            "start_date": start_date,
            "end_date": end_date,
            "operation": operation,
            "adjustment_message": adjustment_message,
            "error": None,
            "today": today.isoformat()
        }
    )

# ==============================
# 🔹 5)   Profit-And-Loss Section's 
# ==============================
@app.get("/profit-loss", response_class=HTMLResponse)
async def profit_loss_page(request: Request):

    today = datetime.today().date()

    return templates.TemplateResponse(
        "profit-loss.html",
        {
            "request": request,
            "today": today.isoformat()
        }
    )


@app.post("/profit-loss", response_class=HTMLResponse)
async def calculate_profit_loss(
    request: Request,
    ticker: str = Form(...),
    buy_date: str = Form(...),
    sell_date: str = Form(...),
    plot: str = Form(None)
):

    ticker = ticker.upper().strip()

    today = datetime.today().date()

    # -------- Validate Dates --------
    try:

        buy_date_obj = datetime.strptime(buy_date, "%Y-%m-%d").date()
        sell_date_obj = datetime.strptime(sell_date, "%Y-%m-%d").date()

        if buy_date_obj > sell_date_obj:
            raise ValueError("Buy date cannot be after Sell date")

        if buy_date_obj > today or sell_date_obj > today:
            raise ValueError("Future dates are not allowed")

    except ValueError as e:

        return templates.TemplateResponse(
            "profit-loss.html",
            {
                "request": request,
                "error": str(e),
                "ticker": ticker,
                "buy_date": buy_date,
                "sell_date": sell_date,
                "today": today.isoformat()
            }
        )

    plot_value = True if plot == "true" else False

    # -------- Run Analyzer --------
    result = Profit_And_Loss_Analyzer(
        ticker=ticker,
        buy_date=buy_date,
        sell_date=sell_date,
        plot=plot_value
    )

    # -------- Handle Invalid Ticker --------
    if result.get("error"): 

        return templates.TemplateResponse(
            "profit-loss.html",
            {
                "request": request,
                "error": result.get("error"),
                "ticker": ticker,
                "buy_date": buy_date,
                "sell_date": sell_date,
                "today": today.isoformat()
            }
        )

    return templates.TemplateResponse(
        "profit-loss.html",
        {
            "request": request,
            "result": result,
            "ticker": ticker,
            "buy_date": buy_date,
            "sell_date": sell_date,
            "today": today.isoformat()
        }
    )



# ==============================
# 🔹 6)   Graph_Plotter Section's 
# ==============================
@app.get("/Graphplotter", response_class=HTMLResponse)
async def graph_plotter_page(request: Request):

    today = datetime.today().date()

    return templates.TemplateResponse(
        "graphplotter.html",
        {
            "request": request,
            "today": today.isoformat()
        }
    )


@app.post("/plot", response_class=HTMLResponse)
async def plot_graph(
    request: Request,
    ticker: str = Form(...),
    start_date: str = Form(None),
    end_date: str = Form(None),
    price_type: str = Form("Close"),
    moving_averages: str = Form(None)
):

    ticker = ticker.upper().strip()

    today = datetime.today().date()

    # -------- Validate Dates --------
    try:

        if start_date:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            if start_date_obj > today:
                raise ValueError("Start date cannot be in the future")

        if end_date:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
            if end_date_obj > today:
                raise ValueError("End date cannot be in the future")

        if start_date and end_date and start_date_obj > end_date_obj:
            raise ValueError("Start date cannot be after End date")

    except ValueError as e:

        return templates.TemplateResponse(
            "graphplotter.html",
            {
                "request": request,
                "error": str(e),
                "ticker": ticker,
                "start_date": start_date,
                "end_date": end_date,
                "today": today.isoformat()
            }
        )

    # -------- Run Graph Plotter --------
    result = Graph_Plotter(
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        price_type=price_type,
        moving_averages=moving_averages,
        plot=True
    )

    # -------- Handle Invalid Ticker / Data Errors --------
    if result.get("error"):

        return templates.TemplateResponse(
            "graphplotter.html",
            {
                "request": request,
                "error": result["error"],
                "ticker": ticker,
                "start_date": start_date,
                "end_date": end_date,
                "today": today.isoformat()
            }
        )

    # -------- Success Case --------
    return templates.TemplateResponse(
        "graphplotter.html",
        {
            "request": request,
            "plot_html": result["plot_html"],
            "ticker": result["ticker"],
            "columns": result["available_columns"],
            "ma_used": result["moving_averages_used"],
            "today": today.isoformat()
        }
    )

# ==============================
# 🔹 6)   Prediction Model Section's 
# ==============================
@app.get("/Predictionmodel", response_class=HTMLResponse)
async def Predictionmodel(request: Request):

    return templates.TemplateResponse(
        "Predictionmodel.html",
        {
            "request": request
        }
    )


@app.post("/predict", response_class=HTMLResponse)
async def predict(request: Request, ticker: str = Form(...)):

    ticker = ticker.upper().strip()

    period = "5y"
    sequence_length = 60
    n_future = 30

    try:
        df = get_fund_data(ticker, period)

        if df is None:
            return templates.TemplateResponse(
                "Predictionmodel.html",
                {
                    "request": request,
                    "error": "Invalid ticker or no market data found.",
                    "ticker": ticker
                }
            )

        future_df = predict_future_prices(df, sequence_length, n_future)

        if future_df is None:
            return templates.TemplateResponse(
                "Predictionmodel.html",
                {
                    "request": request,
                    "error": "Not enough historical data to run prediction.",
                    "ticker": ticker
                }
            )

        current_price = float(df["Close"].iloc[-1])
        future_price = float(future_df["Predicted_Close"].iloc[-1])

        chart_html = plot_prediction(future_df)

        result = {
            "current_price": current_price,
            "predicted_last_price": future_price,
            "signal": generate_signal(current_price, future_price),
            "predictions": future_df.to_dict(orient="records"),
            "chart": chart_html
        }

        return templates.TemplateResponse(
            "Predictionmodel.html",
            {
                "request": request,
                "result": result,
                "ticker": ticker
            }
        )

    except Exception:
        return templates.TemplateResponse(
            "Predictionmodel.html",
            {
                "request": request,
                "error": "Prediction failed. Please try a valid ticker.",
                "ticker": ticker
            }
        )