from flask import Flask, jsonify
from flask_cors import CORS
import yfinance as yf
import pandas as pd
import os

app = Flask(__name__)
CORS(app)
# ✅ List of 50 Indian Stocks (NSE symbols)
INDIAN_STOCKS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "KOTAKBANK.NS", "HINDUNILVR.NS", "LT.NS", "BAJFINANCE.NS", "ITC.NS",
    "ASIANPAINT.NS", "SUNPHARMA.NS", "HCLTECH.NS", "WIPRO.NS", "MARUTI.NS",
    "ULTRACEMCO.NS", "ONGC.NS", "NTPC.NS", "POWERGRID.NS", "BHARTIARTL.NS",
    "SBIN.NS", "GRASIM.NS", "TITAN.NS", "HINDALCO.NS", "JSWSTEEL.NS",
    "COALINDIA.NS", "BPCL.NS", "INDUSINDBK.NS", "ADANIENT.NS", "ADANIPORTS.NS",
    "DRREDDY.NS", "CIPLA.NS", "APOLLOHOSP.NS", "BRITANNIA.NS", "TATAMOTORS.NS",
    "M&M.NS", "EICHERMOT.NS", "HEROMOTOCO.NS", "BAJAJ-AUTO.NS", "SHREECEM.NS",
    "DIVISLAB.NS", "UPL.NS", "TECHM.NS", "ZOMATO.NS", "DLF.NS",
    "GAIL.NS", "PNB.NS", "BANKBARODA.NS", "BHEL.NS", "IRCTC.NS"
]

# ✅ Function to fetch real-time stock data
def fetch_stock_data(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info

        # Fetch financial metrics with fallbacks
        data = {
            "symbol": symbol,
            "roe": info.get('returnOnEquity', 0) or 0,
            "pe_ratio": info.get('trailingPE', 0) or 0,
            "debt_equity": info.get('debtToEquity', 0) or 0,
            "book_value": info.get('bookValue', 0) or 0,
            "roce": info.get('returnOnAssets', 0) or 0   # ROCE proxy
        }
        return data
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

# ✅ Function to rank stocks
def rank_stocks():
    stock_data = [fetch_stock_data(symbol) for symbol in INDIAN_STOCKS]
    
    # Remove failed or empty stock data
    stock_data = [data for data in stock_data if data]

    # ✅ Convert to DataFrame for ranking
    df = pd.DataFrame(stock_data)

    # ✅ Handle missing or empty data
    if df.empty:
        return [{"error": "No valid stock data fetched"}]

    # ✅ Ranking Algorithm
    df['score'] = (
        (df['roe'] * 0.3) +           # ROE weight: 30%
        (df['roce'] * 0.25) -         # ROCE weight: 25%
        (df['pe_ratio'] * -0.2) -     # P/E: lower is better (negative weight)
        (df['debt_equity'] * 0.15) +  # Debt/Equity weight: 15%
        (df['book_value'] * 0.1)      # Book Value weight: 10%
    )

    # ✅ Sort by score (higher = better)
    df = df.sort_values('score', ascending=False)

    # ✅ Convert to list of dicts
    ranked_stocks = df.to_dict(orient='records')
    return ranked_stocks

# ✅ API endpoint
@app.route('/stocks', methods=['GET'])
def get_stocks():
    ranked_stocks = rank_stocks()
    return jsonify(ranked_stocks)

# ✅ Port Binding for Render Deployment
if __name__ == '__main__':
    PORT = int(os.environ.get("PORT", 5000))  # Use Render's port
    print(f"Running on port {PORT}")  # Debug output
    app.run(host='0.0.0.0', port=PORT, debug=True)
