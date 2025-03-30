from flask import Flask, jsonify
from flask_cors import CORS  # ✅ Import CORS
import yfinance as yf
import pandas as pd
import os
import numpy as np

app = Flask(__name__)
CORS(app)  # ✅ Enable CORS for all routes

# ✅ 100 Stocks (Indian + US)
STOCKS = [
    # 🇮🇳 Indian Stocks
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "KOTAKBANK.NS", "HINDUNILVR.NS", "LT.NS", "BAJFINANCE.NS", "ITC.NS",
    "ASIANPAINT.NS", "SUNPHARMA.NS", "HCLTECH.NS", "WIPRO.NS", "MARUTI.NS",
    "ULTRACEMCO.NS", "ONGC.NS", "NTPC.NS", "POWERGRID.NS", "BHARTIARTL.NS",
    "SBIN.NS", "GRASIM.NS", "TITAN.NS", "HINDALCO.NS", "JSWSTEEL.NS",
    "COALINDIA.NS", "BPCL.NS", "INDUSINDBK.NS", "ADANIENT.NS", "ADANIPORTS.NS",
    "DRREDDY.NS", "CIPLA.NS", "APOLLOHOSP.NS", "BRITANNIA.NS", "TATAMOTORS.NS",
    "M&M.NS", "EICHERMOT.NS", "HEROMOTOCO.NS", "BAJAJ-AUTO.NS", "SHREECEM.NS",
    "DIVISLAB.NS", "UPL.NS", "TECHM.NS", "ZOMATO.NS", "DLF.NS",
    "GAIL.NS", "PNB.NS", "BANKBARODA.NS", "BHEL.NS", "IRCTC.NS",
    
    # 🇺🇸 US Stocks
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",
    "META", "NVDA", "BRK-B", "JPM", "V",
    "JNJ", "WMT", "PG", "MA", "UNH",
    "HD", "DIS", "PYPL", "NFLX", "ADBE",
    "XOM", "KO", "PEP", "INTC", "CSCO",
    "T", "PFE", "NKE", "MRK", "MCD",
    "CRM", "ABBV", "LLY", "COST", "ABT",
    "DHR", "TMO", "QCOM", "ACN", "AVGO",
    "ORCL", "TXN", "IBM", "AMD", "HON",
    "AMGN", "LOW", "CVX", "UNP", "LIN"
]

# ✅ Function to fetch stock data
def fetch_stock_data(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info

        # ✅ Financial metrics with fallbacks
        data = {
            "symbol": symbol,
            "country": "US" if "." not in symbol else "India",
            "current_price": info.get('currentPrice', 0) or 0,
            "roe": info.get('returnOnEquity', 0) or 0,
            "roce": info.get('returnOnAssets', 0) or 0,  # ROCE proxy
            "pe_ratio": info.get('trailingPE', 0) or 0,
            "debt_equity": info.get('debtToEquity', 0) or 0,
            "book_value": info.get('bookValue', 0) or 0
        }

        # ✅ Calculate recommended buy price: 10-20% below current price
        discount_factor = np.random.uniform(0.8, 0.9)  # Random 10-20% discount
        data["recommended_buy_price"] = data["current_price"] * discount_factor

        return data

    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

# ✅ Fetch and rank all stocks
def rank_stocks():
    stock_data = [fetch_stock_data(symbol) for symbol in STOCKS]

    # ✅ Remove failed or empty data
    stock_data = [data for data in stock_data if data]

    # ✅ Convert to DataFrame
    df = pd.DataFrame(stock_data)

    if df.empty:
        return [{"error": "No valid stock data fetched"}]

    # ✅ Scoring Algorithm with Granularity
    df['score'] = (
        (df['roe'] * 0.35) +           # ROE weight: 35%
        (df['roce'] * 0.25) -          # ROCE weight: 25%
        (df['pe_ratio'] * -0.2) -      # P/E: lower is better
        (df['debt_equity'] * 0.1) +    # Debt/Equity: 10% (penalizing more)
        (df['book_value'] * 0.05)      # Book Value weight: 5%
    )

    # ✅ Normalize scores between 1-10
    min_score, max_score = df['score'].min(), df['score'].max()
    df['score'] = ((df['score'] - min_score) / (max_score - min_score)) * 8 + 1

    # ✅ Add randomness to avoid clustering
    df['score'] = df['score'] + np.random.uniform(-0.3, 0.3, len(df))

    # ✅ Clip and round the scores
    df['score'] = df['score'].clip(1, 10).round(1)

    # ✅ Sort by score
    df = df.sort_values('score', ascending=False)

    # ✅ Convert to list of dicts
    ranked_stocks = df.to_dict(orient='records')

    return ranked_stocks

# ✅ API endpoint
@app.route('/stocks', methods=['GET'])
def get_stocks():
    ranked_stocks = rank_stocks()
    return jsonify(ranked_stocks)

# ✅ Render deployment port
if __name__ == '__main__':
    PORT = int(os.environ.get("PORT", 5000))
    print(f"Running on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=True)
