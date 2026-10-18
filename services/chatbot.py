import yfinance as yf
import re
import os
from groq import Groq

# Groq Client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# System Prompt 
SYSTEM_PROMPT = """
You are the AI assistant for the Black Soil AI financial dashboard.

Creator: Shriyansh Tiwari.

Your primary role is to help users understand and use the tools available in the platform
and to help them find Yahoo Finance ticker symbols for stocks, ETFs, and funds.

Platform Features:

1. Chatbot (You)
You help users find ticker symbols for companies, ETFs, and financial instruments listed on Yahoo Finance.
You also explain how the dashboard tools work and guide users through the platform.

2. Price Checker
Users can check the latest price of stocks or ETFs using Yahoo Finance data.
This section also provides data visualization for the selected asset.

3. Recent Trend Analysis
Users can analyze recent market trends and visualize price movements using charts.

4. Custom Date Analysis
Users can analyze market performance between custom start and end dates.
This section also includes visualization of the selected data.

5. Profit / Loss Analyzer
Users can calculate profit or loss based on buy price, sell price, and quantity.
Visualization is also provided to help users understand the result.

6. Graph Plotter
Users can generate price charts for financial assets.
This tool also supports moving average indicators to help analyze trends.

7. Prediction Model
This section predicts future price movement using a  Deep learning model.
Unlike other tools, this section does not provide visualization.

Important Guidelines:

• When users ask what you can do or what features the platform provides,
  explain the dashboard tools clearly.

• If a user asks for a ticker symbol, help identify the correct company or fund.

• Keep responses clear, helpful, and concise.

• If the user greets you, respond naturally and politely.
"""


def ask_llm(query):

    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query}
        ]
    )

    return completion.choices[0].message.content.strip()


def extract_company_name(text):

    text = text.lower()

    remove_words = [
        "give me", "ticker", "symbol", "for", "name",
        "of", "what is", "tell me", "the", "find"
    ]

    for word in remove_words:
        text = text.replace(word, "")

    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)

    text = " ".join(text.split())

    return text

def get_yfinance_ticker(company):

    try:
        search = yf.Search(company, max_results=5)

        quotes = search.quotes

        for q in quotes:
            if q.get("quoteType") == "EQUITY":
                return q.get("symbol")

        return None

    except:
        return None

greeting_keywords = [
    "hello","hi","hey","good morning","good afternoon",
    "good evening","greetings","hi there","hello there","hey there"
]

purpose_keywords = [
    "what do you do","what is your purpose","what can you do",
    "how can you help","your purpose"
]

creator_keywords = [
    "who created you","who built you","who made you",
    "who developed you","who is your creator"
]

thanks_keywords = [
    "thanks","thank you","thanks a lot","many thanks"
]

def chatbot(message):

    text = message.lower()

    # Greeting
    if any(word in text for word in greeting_keywords):
        return "Hello! 👋 I'm a financial assistant that helps you find Yahoo Finance ticker symbols."

    # Purpose
    if any(word in text for word in purpose_keywords):
        return "My purpose is to help users quickly find ticker symbols for companies, ETFs, and funds listed on Yahoo Finance."

    # Creator
    if any(word in text for word in creator_keywords):
        return "I was created by Shriyansh Tiwari as part of an AI financial assistant project."

    # Thanks
    if any(word in text for word in thanks_keywords):
        return "You're welcome! 😊"

    # Try ticker lookup
    company = extract_company_name(message)

    ticker = get_yfinance_ticker(company)

    if ticker:
        return f'The Ticker Name For This "{company.title()}" Is "{ticker}"'

    # If not a ticker request → ask LLM
    return ask_llm(message)